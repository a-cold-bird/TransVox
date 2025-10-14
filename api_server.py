#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简易API服务：对外提供视频翻译与配音的一键接口

依赖：
  pip install fastapi uvicorn pydantic

使用：
  uvicorn api_server:app --host 0.0.0.0 --port 8000

接口：
  POST /process
    - form-data 或 JSON：
      - file: 可选（上传视频文件；与 video_path 二选一）
      - video_path: 可选（本地路径；与 file 二选一）
      - source_lang: 可选（默认 auto）
      - target_lang: 必填（indextts: zh/en；gpt-sovits: zh/en/ja/ko）
      - tts_engine: 可选（indextts/gptsovits；默认 indextts）
      - transcribe_engine: 可选（whisperx；默认 whisperx）
      - diarization: 可选（bool，默认 true）
      - separation: 可选（bool，默认 true）

    返回：JSON
      - output_dir, initial_srt, merged_srt, translated_srt, final_video
"""

import os
import sys
import shutil
import subprocess
import logging
import asyncio
import hashlib
import uuid
from collections import deque
from pathlib import Path
from typing import Optional, List
from dataclasses import asdict
import signal
import platform
import time
from datetime import datetime

try:
    import psutil  # 可选，用于递归终止子进程
except Exception:
    psutil = None

try:
    import pynvml  # 用于GPU监控
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except Exception:
    pynvml = None
    GPU_AVAILABLE = False

# 尝试导入工作台模块
try:
    from tools.srt_video_tts_workbench import SRTVideoTTSWorkbench, SubtitleSegment
    WORKBENCH_AVAILABLE = True
except ImportError:
    WORKBENCH_AVAILABLE = False

# 配置日志
def setup_logging():
    """配置日志系统"""
    # 创建logs目录
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # 生成日志文件名（按日期）
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = log_dir / f'api_server_{today}.log'
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置根日志器
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            # 文件处理器
            logging.FileHandler(log_file, encoding='utf-8'),
            # 控制台处理器
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 创建API专用日志器
    api_logger = logging.getLogger('api_server')
    api_logger.setLevel(logging.INFO)
    
    # 设置视频历史相关的日志为DEBUG级别，减少冗余输出
    video_logger = logging.getLogger('api_server.video_history')
    video_logger.setLevel(logging.DEBUG)
    
    return api_logger

# 初始化日志
logger = setup_logging()

# 初始化工作台实例
if WORKBENCH_AVAILABLE:
    workbench = SRTVideoTTSWorkbench("workbench_web")
    logger.info("SRT+视频+TTS工作台已初始化")
else:
    workbench = None
    logger.warning("SRT+视频+TTS工作台不可用")


def _kill_process_tree(pid: int):
    """强制终止进程树，优先使用 psutil；Windows 回退 taskkill /T /F。"""
    try:
        logger.info(f"[cancel] try kill tree pid={pid} psutil={'on' if psutil else 'off'} platform={platform.system()}")
        if psutil:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            try:
                logger.info(f"[cancel] parent={parent.pid} children={[c.pid for c in children]}")
            except Exception:
                pass
            for c in children:
                try:
                    c.terminate()
                except Exception:
                    pass
            try:
                parent.terminate()
            except Exception:
                pass
            gone, alive = psutil.wait_procs([parent] + children, timeout=1.0)
            for a in alive:
                try:
                    a.kill()
                except Exception:
                    pass
            return
        # 无 psutil：Windows 使用 taskkill，其他系统发 SIGTERM/SIGKILL
        if platform.system().lower().startswith('win'):
            try:
                r = subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'], check=False, capture_output=True, text=True)
                logger.info(f"[cancel] taskkill rc={r.returncode} out={r.stdout} err={r.stderr}")
            except Exception:
                pass
        else:
            try:
                # 尝试对进程组发送
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGTERM)
                logger.info(f"[cancel] sent SIGTERM to pgid={pgid}")
            except Exception:
                try:
                    os.kill(pid, signal.SIGTERM)
                    logger.info(f"[cancel] sent SIGTERM to pid={pid}")
                except Exception:
                    pass
            try:
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGKILL)
                logger.info(f"[cancel] sent SIGKILL to pgid={pgid}")
            except Exception:
                try:
                    os.kill(pid, signal.SIGKILL)
                    logger.info(f"[cancel] sent SIGKILL to pid={pid}")
                except Exception:
                    pass
    except Exception:
        pass

from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
# 读取 .env（UTF-8），供本服务使用
def _load_dotenv_into_environ():
    try:
        root = Path(__file__).resolve().parent
        candidates = [root / '.env', root.parent / '.env']
        for p in candidates:
            if p.exists():
                with open(p, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            k, v = line.split('=', 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            os.environ.setdefault(k, v)
                logger.info(f"已从 .env 加载环境变量: {p}")
                break
    except Exception as e:
        logger.warning(f"加载 .env 失败: {e}")

# 注意：需在logger初始化后再调用
_load_dotenv_into_environ()

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / 'Scripts'

# 将 Scripts 目录添加到 sys.path，以便导入工具模块
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    async def _startup_worker():
        async def _job_worker():
            global RUNNING_JOB, CURRENT_RUNNING
            while True:
                try:
                    if RUNNING_JOB is None and JOB_QUEUE:
                        job = JOB_QUEUE.popleft()
                        RUNNING_JOB = job
                        CURRENT_RUNNING = job['job_id']
                        job_id = job['job_id']
                        JOB_STATUS[job_id] = {'status': 'running', 'step': 'start', 'progress': 0, 'user_id': job.get('user_id'), 'ts': time.time()}
                        await _execute_job(job)
                        RUNNING_JOB = None
                        CURRENT_RUNNING = None
                    else:
                        await asyncio.sleep(0.3)
                except Exception as e:
                    logger.error(f"worker error: {e}")
                    await asyncio.sleep(0.5)
        asyncio.create_task(_job_worker())
    
    # 启动
    await _startup_worker()
    yield
    
    # 关闭时执行
    try:
        logger.info('API 正在关闭，开始清理子进程...')
        # 终止运行中的作业进程
        try:
            if RUNNING_JOB:
                jid = RUNNING_JOB.get('job_id')
                proc = PROCESS_MAP.get(jid)
                if proc and proc.poll() is None:
                    logger.info(f'终止运行中的作业: {jid} pid={proc.pid}')
                    _kill_process_tree(proc.pid)
        except Exception as e:
            logger.warning(f'清理运行中作业失败: {e}')

        # 终止所有登记的进程
        try:
            for jid, proc in list(PROCESS_MAP.items()):
                if proc and proc.poll() is None:
                    logger.info(f'终止登记进程: {jid} pid={proc.pid}')
                    _kill_process_tree(proc.pid)
        except Exception as e:
            logger.warning(f'清理登记进程失败: {e}')

        # 清空队列与映射
        try:
            JOB_QUEUE.clear()
            PROCESS_MAP.clear()
        except Exception:
            pass
        logger.info('子进程清理完成。')
    except Exception as e:
        logger.warning(f'关闭清理异常: {e}')

app = FastAPI(title="Video Translate API", version="1.0.0", lifespan=lifespan)

# CORS（前端本地文件/不同端口访问时允许）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态前端挂载
web_dir = Path('web')
web_dir.mkdir(parents=True, exist_ok=True)
# 挂载在 /web，避免拦截 /process 等API路由
app.mount('/web', StaticFiles(directory=str(web_dir), html=True), name='web')
# 挂载输出目录，便于前端视频预览
out_static = Path('output')
out_static.mkdir(parents=True, exist_ok=True)
app.mount('/output', StaticFiles(directory=str(out_static), html=False), name='output')
# 只读挂载 input 目录，便于预设视频预览
in_static = Path('input')
in_static.mkdir(parents=True, exist_ok=True)
app.mount('/input', StaticFiles(directory=str(in_static), html=False), name='input')
# 并发控制：同一时间仅允许1个任务执行
_EXEC_SEMA = asyncio.Semaphore(1)
JOB_STATUS: dict = {}
CURRENT_RUNNING: Optional[str] = None
JOB_QUEUE = deque()  # queue of job dicts
RUNNING_JOB: Optional[dict] = None
PROCESS_MAP: dict = {}

# 限制：从环境变量加载（默认：20分钟、1GB）
# 可通过环境变量调整：
# MAX_VIDEO_MINUTES=30  # 最大时长（分钟）
# MAX_VIDEO_BYTES=2147483648  # 最大文件大小（字节，2GB）
MAX_VIDEO_MINUTES = int(os.getenv('MAX_VIDEO_MINUTES', '20'))
MAX_VIDEO_BYTES = int(os.getenv('MAX_VIDEO_BYTES', str(1024 * 1024 * 1024)))


@app.get('/')
def root():
    # 访问根路径时跳转到 /web/
    return RedirectResponse(url='/web/')


@app.get('/api/health')
def health():
    """健康检查端点"""
    return {"status": "ok", "service": "TransVox API", "version": "1.0.0"}




async def _execute_job(job: dict):
    """Execute a queued job with cancel support and post-move outputs."""
    job_id = job['job_id']
    user_id = job['user_id']
    video = Path(job['video'])
    stem = video.stem
    skip_tts = job['skip_tts']
    source_lang = job['source_lang']
    target_lang = job['target_lang']
    transcribe_engine = job['transcribe_engine']
    tts_engine_norm = job['tts_engine']
    diarization = job['diarization']
    separation = job['separation']
    speed_factor = job['speed_factor']

    def _run(cmd, env=None):
        creationflags = 0
        preexec_fn = None
        try:
            # Windows: 新进程组，便于 taskkill /T /F
            if platform.system().lower().startswith('win'):
                creationflags = getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
            else:
                # POSIX: 独立进程组，便于 killpg
                import os
                preexec_fn = os.setsid
        except Exception:
            pass
        # 设置子进程环境变量，确保UTF-8编码
        if env is None:
            env = os.environ.copy()
        else:
            env = env.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        proc = subprocess.Popen(cmd, env=env, creationflags=creationflags, preexec_fn=preexec_fn)
        PROCESS_MAP[job_id] = proc
        return proc

    try:
        if skip_tts:
            out_dir_tmp = (Path('output') / user_id / job_id / stem).resolve()
            out_dir_tmp.mkdir(parents=True, exist_ok=True)
            cmd_a = [
                sys.executable, 'stepA_prepare_and_blank_srt.py',
                str(video), '-o', str(out_dir_tmp), '-e', transcribe_engine,
            ]
            if str(source_lang).lower() == 'auto':
                cmd_a.extend(['-l', 'auto'])
            if not diarization:
                cmd_a.append('--no-diarize')
            if not separation:
                cmd_a.append('--no-separation')
            JOB_STATUS[job_id] = {'status': 'running', 'step': 'stepA', 'progress': 20, 'user_id': user_id, 'ts': time.time()}
            p1 = _run(cmd_a)
            while p1.poll() is None:
                if JOB_STATUS.get(job_id, {}).get('cancel'):
                    _kill_process_tree(p1.pid)
                    JOB_STATUS[job_id] = {'status': 'cancelled', 'step': 'cancelled', 'progress': 0}
                    # 清理运行状态
                    if RUNNING_JOB and RUNNING_JOB.get('job_id') == job_id:
                        globals()['RUNNING_JOB'] = None
                        globals()['CURRENT_RUNNING'] = None
                        logger.info(f"[任务取消] 释放运行资源: {job_id}")
                    return
                await asyncio.sleep(0.5)
            if p1.returncode != 0:
                JOB_STATUS[job_id] = {'status': 'failed', 'step': 'stepA', 'progress': 0}
                # 清理运行状态
                if RUNNING_JOB and RUNNING_JOB.get('job_id') == job_id:
                    globals()['RUNNING_JOB'] = None
                    globals()['CURRENT_RUNNING'] = None
                    logger.info(f"[任务失败] 释放运行资源: {job_id}")
                return
            srt_file = out_dir_tmp / f"{stem}.srt"
            translated_srt = out_dir_tmp / f"{stem}.translated.srt"
            cmd_t = [
                sys.executable, 'Scripts/step4_translate_srt.py',
                str(srt_file), '--target_lang', target_lang, '--whole_file',
                '-o', str(translated_srt)
            ]
            JOB_STATUS[job_id] = {'status': 'running', 'step': 'translate', 'progress': 60, 'user_id': user_id, 'ts': time.time()}
            p2 = _run(cmd_t)
            while p2.poll() is None:
                if JOB_STATUS.get(job_id, {}).get('cancel'):
                    _kill_process_tree(p2.pid)
                    JOB_STATUS[job_id] = {'status': 'cancelled', 'step': 'cancelled', 'progress': 0}
                    # 清理运行状态
                    if RUNNING_JOB and RUNNING_JOB.get('job_id') == job_id:
                        globals()['RUNNING_JOB'] = None
                        globals()['CURRENT_RUNNING'] = None
                        logger.info(f"[任务取消] 释放运行资源: {job_id}")
                    return
                await asyncio.sleep(0.5)
            if p2.returncode != 0:
                JOB_STATUS[job_id] = {'status': 'failed', 'step': 'translate', 'progress': 0}
                # 清理运行状态
                if RUNNING_JOB and RUNNING_JOB.get('job_id') == job_id:
                    globals()['RUNNING_JOB'] = None
                    globals()['CURRENT_RUNNING'] = None
                    logger.info(f"[任务失败] 释放运行资源: {job_id}")
                return
            out_tmp = out_dir_tmp
        else:
            # full pipeline via full_auto_pipeline → 输出到命名空间目录
            ns_out_dir = (Path('output') / user_id / job_id / stem).resolve()
            ns_out_dir.mkdir(parents=True, exist_ok=True)
            JOB_STATUS[job_id] = {'status': 'running', 'step': '准备启动流水线', 'progress': 5, 'user_id': user_id, 'ts': time.time()}

            # 执行流水线并检查返回值
            pipeline_success = await asyncio.get_event_loop().run_in_executor(None, lambda: _run_full_pipeline(
                video_path=video,
                target_lang=target_lang,
                transcribe_engine=transcribe_engine,
                source_lang=source_lang,
                tts_engine=tts_engine_norm,
                diarization=bool(diarization),
                separation=bool(separation),
                speed_factor=speed_factor,
                output_dir=ns_out_dir,
                job_id=job_id,
                user_id=user_id,
            ))

            # 检查流水线是否成功执行
            if not pipeline_success:
                logger.error(f"[任务失败] 流水线执行失败: {job_id}")

                # 获取详细错误信息（如果 _run_full_pipeline 已经更新了）
                current_status = JOB_STATUS.get(job_id, {})
                error_msg = current_status.get('pipeline_error', '流水线执行失败，请查看日志获取详细信息')
                error_details = current_status.get('error_details', '')

                JOB_STATUS[job_id] = {
                    'status': 'failed',
                    'step': 'pipeline_failed',
                    'progress': 0,
                    'error': error_msg,
                    'error_details': error_details,
                    'user_id': user_id,
                    'ts': time.time()
                }
                # 清理运行状态
                if RUNNING_JOB and RUNNING_JOB.get('job_id') == job_id:
                    globals()['RUNNING_JOB'] = None
                    globals()['CURRENT_RUNNING'] = None
                    logger.info(f"[任务失败] 释放运行资源: {job_id}")
                return

            out_tmp = ns_out_dir

        # 直接使用命名空间输出目录
        final_out_dir = out_tmp

        data = _collect_outputs_from_dir(final_out_dir, stem)
        data.update({
            'user_id': user_id,
            'job_id': job_id,
            'video_stem': stem,
            'engine': transcribe_engine,
            'tts_engine': tts_engine_norm,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'skip_tts': bool(skip_tts)
        })
        JOB_STATUS[job_id] = {'status': 'succeeded', 'step': 'done', 'progress': 100, 'data': data, 'user_id': user_id, 'ts': time.time()}
    except Exception as e:
        logger.error(f"job failed: {e}")
        JOB_STATUS[job_id] = {'status': 'failed', 'step': 'exception', 'progress': 0, 'error': str(e), 'user_id': user_id, 'ts': time.time()}
    finally:
        PROCESS_MAP.pop(job_id, None)
        # 清理运行状态，防止任务结束后仍显示为活动任务
        if RUNNING_JOB and RUNNING_JOB.get('job_id') == job_id:
            globals()['RUNNING_JOB'] = None
            globals()['CURRENT_RUNNING'] = None
            logger.info(f"[任务完成] 释放运行资源: {job_id}")


@app.get('/whoami')
def whoami(request: Request):
    user_id = _get_user_id(request)
    # 当前排队人数：运行中(0或1) + 队列长度
    qlen = len(JOB_QUEUE)
    if RUNNING_JOB is not None:
        qlen = qlen + 1
    latest = _find_latest_job_for_user(user_id)
    return {'user_id': user_id, 'queue_len': qlen, 'latest': latest}


@app.get('/progress')
def progress(job_id: str):
    data = JOB_STATUS.get(job_id)
    if not data:
        return JSONResponse({'error': 'job_id not found'}, status_code=404)
    return data


@app.get('/api/pipeline/status/{taskId}')
async def get_pipeline_status(taskId: str):
    """
    获取流水线任务状态API - 返回标准的 ProcessingTask 格式
    """
    try:
        # 查找任务状态
        job_status = JOB_STATUS.get(taskId)

        if not job_status:
            # 任务不存在时，返回cancelled状态而不是404
            # 这样前端可以正确清除进度条
            logger.info(f"[流水线状态] 任务不存在，返回cancelled状态: {taskId}")
            return JSONResponse({
                'success': True,
                'data': {
                    'id': taskId,
                    'videoId': '',
                    'type': 'full_pipeline',
                    'status': 'error',  # 前端的error状态会停止轮询
                    'progress': 0,
                    'message': '任务已被清除或中断',
                    'result': None,
                    'createdAt': time.time(),
                    'updatedAt': time.time()
                }
            })

        # 映射后端状态到前端状态
        status_map = {
            'queued': 'idle',
            'running': 'processing',
            'succeeded': 'completed',
            'failed': 'error',
            'cancelled': 'error'
        }

        frontend_status = status_map.get(job_status.get('status', 'queued'), 'idle')

        # 构建前端期望的响应格式
        response_data = {
            'id': taskId,
            'videoId': job_status.get('data', {}).get('video_stem', ''),
            'type': 'full_pipeline',
            'status': frontend_status,
            'progress': job_status.get('progress', 0),
            'message': job_status.get('step', ''),
            'result': job_status.get('data'),
            'createdAt': job_status.get('ts', time.time()),
            'updatedAt': job_status.get('ts', time.time())
        }

        # 如果任务失败，添加错误信息到响应中
        if frontend_status == 'error' and 'error' in job_status:
            response_data['message'] = job_status.get('error', '处理失败')
            if not response_data['result']:
                response_data['result'] = {}
            response_data['result']['error'] = job_status.get('error_details', job_status.get('error', '未知错误'))

        logger.info(f"[流水线状态] 任务 {taskId}: {frontend_status} ({job_status.get('progress', 0)}%)")

        return JSONResponse({
            'success': True,
            'data': response_data
        })

    except Exception as e:
        logger.error(f"[流水线状态] 查询失败: {e}", exc_info=True)
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/pipeline/stop/{taskId}')
async def stop_pipeline(request: Request, taskId: str):
    """
    停止流水线任务API - 取消正在运行的任务
    """
    try:
        logger.info(f"[流水线停止] 收到停止请求: {taskId}")

        # 查找任务
        job_status = JOB_STATUS.get(taskId)
        if not job_status:
            return JSONResponse({
                'success': False,
                'error': 'Task not found'
            }, status_code=404)

        # 获取用户ID
        user_id = _get_user_id(request)

        # 验证用户权限
        owner = job_status.get('data', {}).get('user_id') or job_status.get('user_id')
        if owner and owner != user_id:
            logger.warning(f"[流水线停止] 权限不足: user={user_id} owner={owner}")
            return JSONResponse({
                'success': False,
                'error': '您没有权限停止此任务'
            }, status_code=403)

        # 从队列中移除（如果还在队列中）
        removed = False
        try:
            for job in list(JOB_QUEUE):
                if job.get('job_id') == taskId:
                    JOB_QUEUE.remove(job)
                    removed = True
                    logger.info(f"[流水线停止] 从队列中移除任务: {taskId}")
                    break
        except Exception:
            pass

        if removed:
            JOB_STATUS[taskId] = {'status': 'cancelled', 'step': 'cancelled', 'progress': 0, 'user_id': user_id, 'ts': time.time()}
            return JSONResponse({
                'success': True,
                'message': '任务已从队列中取消'
            })

        # 终止正在运行的进程
        proc = PROCESS_MAP.get(taskId)
        if proc is not None:
            try:
                logger.info(f"[流水线停止] 终止进程: pid={proc.pid}")
                _kill_process_tree(proc.pid)
            except Exception as e:
                logger.warning(f"[流水线停止] 终止进程失败: {e}")
            finally:
                PROCESS_MAP.pop(taskId, None)

        # 标记为已取消
        JOB_STATUS[taskId] = {'status': 'cancelled', 'step': 'cancelled', 'progress': 0, 'user_id': user_id, 'ts': time.time()}

        # 如果是当前运行的任务，释放资源
        if RUNNING_JOB and RUNNING_JOB.get('job_id') == taskId:
            globals()['RUNNING_JOB'] = None
            globals()['CURRENT_RUNNING'] = None
            logger.info(f"[流水线停止] 释放运行资源: {taskId}")

        return JSONResponse({
            'success': True,
            'message': '任务已停止'
        })

    except Exception as e:
        logger.error(f"[流水线停止] 失败: {e}", exc_info=True)
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.delete('/api/pipeline/clear/{taskId}')
async def clear_pipeline_task(request: Request, taskId: str):
    """
    清除流水线任务状态 - 强制删除任务记录（用于清理卡住的进度条）
    """
    try:
        logger.info(f"[流水线清理] 收到清理请求: {taskId}")

        # 查找任务
        job_status = JOB_STATUS.get(taskId)

        # 如果任务存在，验证用户权限
        if job_status:
            user_id = _get_user_id(request)
            owner = job_status.get('data', {}).get('user_id') or job_status.get('user_id')

            if owner and owner != user_id:
                logger.warning(f"[流水线清理] 权限不足: user={user_id} owner={owner}")
                return JSONResponse({
                    'success': False,
                    'error': '您没有权限清理此任务'
                }, status_code=403)

            # 如果任务还在运行，先尝试停止
            if job_status.get('status') == 'running':
                proc = PROCESS_MAP.get(taskId)
                if proc is not None:
                    try:
                        logger.info(f"[���水线清理] 先停止运行中的进程: pid={proc.pid}")
                        _kill_process_tree(proc.pid)
                        PROCESS_MAP.pop(taskId, None)
                    except Exception as e:
                        logger.warning(f"[流水线清理] 停止进程失败: {e}")

        # 删除实际文件夹
        try:
            import shutil
            user_id = _get_user_id(request)
            job_dir = Path('output') / user_id / taskId
            if job_dir.exists():
                logger.info(f"[流水线清理] 删除文件夹: {job_dir}")
                shutil.rmtree(job_dir)
                logger.info(f"[流水线清理] 文件夹已删除")
            else:
                logger.info(f"[流水线清理] 文件夹不存在: {job_dir}")
        except Exception as e:
            logger.warning(f"[流水线清理] 删除文件夹失败: {e}")

        # 从所有数据结构中移除任务
        JOB_STATUS.pop(taskId, None)
        PROCESS_MAP.pop(taskId, None)

        # 从队列中移除
        try:
            for job in list(JOB_QUEUE):
                if job.get('job_id') == taskId:
                    JOB_QUEUE.remove(job)
                    break
        except Exception:
            pass

        # 如果是当前运行的任务，释放资源
        if RUNNING_JOB and RUNNING_JOB.get('job_id') == taskId:
            globals()['RUNNING_JOB'] = None
            globals()['CURRENT_RUNNING'] = None
            logger.info(f"[流水线清理] 释放运行资源: {taskId}")

        logger.info(f"[流水线清理] 任务已清除: {taskId}")
        return JSONResponse({
            'success': True,
            'message': '任务状态已清除'
        })

    except Exception as e:
        logger.error(f"[流水线清理] 失败: {e}", exc_info=True)
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.get('/api/pipeline/history')
async def get_pipeline_history(request: Request):
    """
    获取流水线历史任务列表 - 通过扫描output文件夹获取用户的所有历史任务

    返回格式：
    {
        "success": true,
        "data": [
            {
                "id": "task_id",
                "videoName": "video.mp4",
                "status": "completed",
                "createdAt": 1234567890.123,
                "config": {...},
                "result": {
                    "finalVideo": "path/to/video.mp4",
                    "srtFiles": ["path/to/file.srt", ...]
                }
            }
        ]
    }
    """
    try:
        user_id = _get_user_id(request)
        logger.info(f"[历史记录] 用户请求历史任务: {user_id}")

        # 扫描output文件夹
        output_base = Path('output') / user_id
        history_tasks = []

        if output_base.exists():
            # 遍历用户的所有任务目录
            for job_dir in output_base.iterdir():
                if not job_dir.is_dir():
                    continue

                job_id = job_dir.name

                # 在任务目录下查找视频目录
                for video_dir in job_dir.iterdir():
                    if not video_dir.is_dir():
                        continue

                    video_stem = video_dir.name

                    # 查找最终视频文件
                    final_video = None
                    srt_files = []

                    # 查找 merge 子目录
                    merge_dir = video_dir / 'merge'
                    if merge_dir.exists():
                        # 查找最终视频（通常是*_final.mp4或类似的）
                        for video_file in merge_dir.glob('*.mp4'):
                            if 'final' in video_file.name.lower() or 'dubbed' in video_file.name.lower():
                                final_video = str(video_file.relative_to(Path('output')))
                                break
                        # 如果没找到final，使用任何mp4
                        if not final_video:
                            for video_file in merge_dir.glob('*.mp4'):
                                final_video = str(video_file.relative_to(Path('output')))
                                break

                    # 如果merge目录没有找到，直接在视频目录查找
                    if not final_video:
                        for video_file in video_dir.glob('*.mp4'):
                            if 'final' in video_file.name.lower() or 'dubbed' in video_file.name.lower():
                                final_video = str(video_file.relative_to(Path('output')))
                                break

                    # 查找SRT文件
                    for srt_file in video_dir.glob('**/*.srt'):
                        # 跳过merged_optimized文件
                        if '_merged_optimized' in srt_file.name:
                            continue
                        srt_files.append({
                            'name': srt_file.name,
                            'path': str(srt_file.relative_to(Path('output')))
                        })

                    # 如果找到了视频文件，添加到历史记录
                    if final_video:
                        # 获取目录创建时间
                        created_at = video_dir.stat().st_ctime

                        task_item = {
                            'id': job_id,
                            'videoName': video_stem,
                            'status': 'completed',
                            'createdAt': created_at,
                            'config': {
                                'sourceLanguage': 'auto',
                                'targetLanguage': 'unknown',
                                'ttsEngine': 'unknown'
                            },
                            'result': {
                                'finalVideo': final_video,
                                'srtFiles': srt_files
                            }
                        }

                        history_tasks.append(task_item)

        # 按创建时间倒序排列（最新的在前）
        history_tasks.sort(key=lambda x: x['createdAt'], reverse=True)

        logger.info(f"[历史记录] 返回 {len(history_tasks)} 个历史任务")
        return JSONResponse({
            'success': True,
            'data': history_tasks
        })

    except Exception as e:
        logger.error(f"[历史记录] 获取失败: {e}", exc_info=True)
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/cancel')
async def cancel(request: Request, job_id: str = Form(...)):
    logger.info(f"/cancel called from {request.client.host if request.client else 'unknown'} job_id={job_id}")
    st = JOB_STATUS.get(job_id)
    if not st:
        logger.warning(f"/cancel job not found: {job_id}")
        return JSONResponse({'error': 'job_id not found'}, status_code=404)
    user_id = _get_user_id(request)
    # 仅允许取消自己的任务
    owner = st.get('data', {}).get('user_id') or st.get('user_id')
    if owner and owner != user_id:
        logger.warning(f"/cancel forbidden user={user_id} owner={owner} job_id={job_id}")
        return JSONResponse({'error': 'forbidden'}, status_code=403)

    # 如果在队列中，直接移除
    removed = False
    try:
        for i, job in enumerate(list(JOB_QUEUE)):
            if job.get('job_id') == job_id and job.get('user_id') == user_id:
                JOB_QUEUE.remove(job)
                removed = True
                break
    except Exception:
        pass
    if removed:
        logger.info(f"/cancel removed from queue job_id={job_id}")
        JOB_STATUS[job_id] = {'status': 'cancelled', 'step': 'cancelled', 'progress': 0, 'user_id': user_id}
        return {'status': 'ok', 'cancelled': 'queued'}

    # 若在运行中或已启动子进程，标记并尝试终止
    st['cancel'] = True
    st['user_id'] = owner or user_id
    JOB_STATUS[job_id] = st
    proc = PROCESS_MAP.get(job_id)
    if proc is not None:
        try:
            logger.info(f"/cancel terminating running job_id={job_id} pid={proc.pid}")
            _kill_process_tree(proc.pid)
        except Exception as e:
            logger.warning(f"/cancel kill tree error: {e}")
        finally:
            try:
                PROCESS_MAP.pop(job_id, None)
            except Exception:
                pass
    else:
        logger.info(f"/cancel no proc found in PROCESS_MAP for job_id={job_id}")
    # 立即标记为已取消，前端可立刻看到效果
    JOB_STATUS[job_id] = {'status': 'cancelled', 'step': 'cancelled', 'progress': 0, 'user_id': user_id, 'ts': time.time()}
    # 若当前运行就是该作业，解除占用
    try:
        if RUNNING_JOB and RUNNING_JOB.get('job_id') == job_id:
            logger.info(f"/cancel releasing RUNNING_JOB for job_id={job_id}")
            globals()['RUNNING_JOB'] = None
            globals()['CURRENT_RUNNING'] = None
    except Exception:
        pass
    return {'status': 'success', 'cancelled': True}


def _ensure_input_dir() -> Path:
    in_dir = Path('input')
    in_dir.mkdir(parents=True, exist_ok=True)
    return in_dir


def _stem_from_path(video_path: Path) -> str:
    return video_path.stem


def _get_user_id(request: Request) -> str:
    """根据浏览器标识生成用户id（基于UA+Accept-Lang）。"""
    ua = request.headers.get('user-agent', 'unknown')
    al = request.headers.get('accept-language', 'unknown')
    raw = f"{ua}|{al}".encode('utf-8', errors='ignore')
    return hashlib.sha1(raw).hexdigest()[:16]


def _user_has_active_job(user_id: str) -> Optional[str]:
    """同一用户是否已有运行中或排队中的任务，返回已有 job_id 或 None。"""
    # 运行中的
    if RUNNING_JOB and RUNNING_JOB.get('user_id') == user_id:
        return RUNNING_JOB.get('job_id')
    # 队列中的（取最早一个）
    for job in JOB_QUEUE:
        if job.get('user_id') == user_id:
            return job.get('job_id')
    # 已登记但未清理的状态
    for jid, st in JOB_STATUS.items():
        if st.get('status') in ('queued', 'running') and st.get('user_id') == user_id:
            return jid
    return None


def _new_job_id() -> str:
    return uuid.uuid4().hex


def _get_system_stats() -> dict:
    """获取系统GPU和内存状态信息"""
    stats = {
        'gpu_available': GPU_AVAILABLE,
        'gpus': [],
        'system_memory': {}
    }

    # 获取系统内存信息
    if psutil:
        try:
            mem = psutil.virtual_memory()
            stats['system_memory'] = {
                'total_gb': round(mem.total / (1024**3), 2),
                'used_gb': round(mem.used / (1024**3), 2),
                'available_gb': round(mem.available / (1024**3), 2),
                'percent': round(mem.percent, 1)
            }
        except Exception as e:
            logger.warning(f"[系统监控] 无法获取内存信息: {e}")
            stats['system_memory'] = {
                'total_gb': 0,
                'used_gb': 0,
                'available_gb': 0,
                'percent': 0
            }

    # 获取GPU信息
    if GPU_AVAILABLE and pynvml:
        try:
            device_count = pynvml.nvmlDeviceGetCount()
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)

                # 获取内存信息
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

                # 获取利用率
                try:
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_util = util.gpu
                except:
                    gpu_util = 0

                # 获取温度
                try:
                    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except:
                    temp = 0

                # 获取功率
                try:
                    power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # mW to W
                    power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000
                except:
                    power_usage = 0
                    power_limit = 0

                gpu_info = {
                    'index': i,
                    'name': name.decode('utf-8') if isinstance(name, bytes) else name,
                    'memory': {
                        'total_gb': round(mem_info.total / (1024**3), 2),
                        'used_gb': round(mem_info.used / (1024**3), 2),
                        'free_gb': round(mem_info.free / (1024**3), 2),
                        'percent': round(mem_info.used / mem_info.total * 100, 1)
                    },
                    'utilization': gpu_util,
                    'temperature': temp,
                    'power': {
                        'usage_w': round(power_usage, 1),
                        'limit_w': round(power_limit, 1)
                    }
                }
                stats['gpus'].append(gpu_info)
        except Exception as e:
            logger.warning(f"[系统监控] 无法获取GPU信息: {e}")

    return stats


def _resolve_out_dir(stem: str, user_id: Optional[str] = None, job_id: Optional[str] = None) -> Optional[Path]:
    """根据新/旧规则解析输出目录。
    优先使用 output/<user>/<job>/<stem>，否则回退到 output/<stem>（兼容旧路径）。
    如果未提供 user/job，则尝试在 output/*/*/<stem> 中找到最新的一个。
    """
    base = Path('output')
    # 指定用户与作业
    if user_id and job_id:
        candidate = base / user_id / job_id / stem
        if candidate.exists():
            return candidate
    # 扫描最新
    try:
        newest = None
        for user_dir in base.iterdir():
            if not user_dir.is_dir():
                continue
            for job_dir in user_dir.iterdir():
                if not job_dir.is_dir():
                    continue
                d = job_dir / stem
                if d.exists() and d.is_dir():
                    mtime = d.stat().st_mtime
                    if newest is None or mtime > newest[0]:
                        newest = (mtime, d)
        if newest:
            return newest[1]
    except Exception:
        pass
    # 旧路径回退
    legacy = base / stem
    return legacy if legacy.exists() else None


def _find_latest_job_for_user(user_id: str) -> Optional[dict]:
    """返回用户最近的一个作业状态（优先带 data 的 succeeded/running/queued）。"""
    # 优先在 JOB_STATUS 里找最新的
    latest = None
    for jid, st in JOB_STATUS.items():
        uid = st.get('data', {}).get('user_id') or st.get('user_id')
        if uid != user_id:
            continue
        ts = st.get('ts') or 0
        if latest is None or ts > latest[0]:
            latest = (ts, {'job_id': jid, 'status': st.get('status'), 'data': st.get('data'), 'progress': st.get('progress'), 'step': st.get('step')})
    if latest:
        return latest[1]
    # 回退：查找 output/user_id 下修改时间最新的 job 目录
    base = Path('output') / user_id
    if base.exists():
        cand = None
        for job_dir in base.iterdir():
            if not job_dir.is_dir():
                continue
            mtime = job_dir.stat().st_mtime
            if cand is None or mtime > cand[0]:
                cand = (mtime, job_dir)
        if cand:
            job_dir = cand[1]
            # 尝试推断 stem
            stems = [p.stem for p in job_dir.iterdir() if p.is_dir()]
            stem = stems[0] if stems else None
            data = None
            if stem:
                out_dir = job_dir / stem
                if out_dir.exists():
                    data = _collect_outputs_from_dir(out_dir, stem)
                    data.update({'user_id': user_id, 'job_id': job_dir.name, 'video_stem': stem})
            return {'job_id': job_dir.name, 'status': 'unknown', 'data': data, 'progress': None, 'step': None}
    return None


def _parse_pipeline_progress(line: str) -> Optional[tuple]:
    """
    解析流水线输出日志，提取步骤和进度信息

    返回: (step_name, progress_percent) 或 None
    """
    line = line.strip()

    # 启动流水线
    if '开始全自动视频翻译流水线' in line:
        return ('pipeline_start', 5)

    # 步骤1: 音视频处理和转录 (5-35%)
    if '[Step 1]' in line:
        if '音视频处理和转录' in line:
            return ('audio_separation', 10)
        elif '完成' in line:
            return ('audio_separation_done', 35)
    elif 'stepA' in line.lower() or '分离音频' in line:
        return ('audio_processing', 15)
    elif 'whisperx' in line.lower() or '转录' in line:
        return ('transcription', 20)
    elif '说话人识别' in line or 'diarization' in line.lower():
        return ('diarization', 25)

    # 步骤2: 翻译字幕 (35-55%)
    elif '[Step 2]' in line:
        if '翻译字幕' in line:
            return ('translation', 40)
        elif '完成' in line:
            return ('translation_done', 55)
    elif 'step4_translate' in line.lower() or '翻译中' in line:
        return ('translating', 45)

    # 步骤3: TTS语音合成 (55-85%)
    elif '[Step 3]' in line:
        if 'IndexTTS' in line or 'GPT-SoVITS' in line:
            return ('tts_synthesis', 60)
        elif '完成' in line:
            return ('tts_done', 85)
    elif 'stepB' in line.lower() or 'TTS' in line:
        return ('tts_processing', 65)
    elif '生成TTS音频' in line or 'generating audio' in line.lower():
        return ('tts_generating', 75)

    # 音视频合并 (85-95%)
    elif 'merge' in line.lower() or '合并' in line:
        if '开始' in line or 'start' in line.lower():
            return ('merging_start', 88)
        elif '完成' in line or 'done' in line.lower():
            return ('merging_done', 95)
        else:
            return ('merging', 90)

    # 流水线完成 (95-100%)
    elif '流水线执行完成' in line or '所有步骤已完成' in line:
        return ('completed', 98)
    elif '最终视频' in line or 'final video' in line.lower():
        return ('final_video', 96)

    return None


def _run_full_pipeline(
    video_path: Path,
    target_lang: str,
    transcribe_engine: str = 'whisperx',
    source_lang: str = 'auto',
    tts_engine: str = 'indextts',
    diarization: bool = True,
    separation: bool = True,
    speed_factor: Optional[float] = None,
    output_dir: Optional[Path] = None,
    job_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> bool:
    """
    调用 full_auto_pipeline.py 执行完整流程，���时追踪进度。

    注意：full_auto_pipeline.py 会自动将输出保存到 output/<video_stem>/
    我们稍后会将文件移动到指定的命名空间目录
    """
    cmd = [
        sys.executable, 'full_auto_pipeline.py',
        str(video_path),
        '--engine', transcribe_engine,
        '--target_lang', target_lang,
        '--tts_engine', tts_engine,
        '--translation_mode', 'whole',
    ]

    # full_auto_pipeline.py 不接受 -o 参数，它会自动输出到 output/<video_stem>/
    # 注意：不要添加 -o 参数！

    # gpt-sovits 默认使用本地模式
    if str(tts_engine).lower().replace('-', '') == 'gptsovits':
        cmd.extend(['--tts_mode', 'local'])
    # full_auto_pipeline 仅支持 language=auto；非 auto 时暂不传递 --language
    if str(source_lang).lower() == 'auto':
        cmd.extend(['--language', 'auto'])
    if not diarization:
        cmd.append('--no-diarization')
    if not separation:
        cmd.append('--no-separation')

    # 环境变量
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    # 仅在 gpt-sovits 时传递语速参数到后续流程（通过环境变量）
    if tts_engine == 'gptsovits' and speed_factor is not None:
        env['GSV_SPEED_FACTOR'] = str(speed_factor)

    # 使用 Popen 实时读取输出
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )

        # 将进程加入 PROCESS_MAP，以便停止时可以终止
        if job_id:
            PROCESS_MAP[job_id] = process
            logger.info(f"[Pipeline] 流水线进程已加入 PROCESS_MAP: job_id={job_id}, pid={process.pid}")

        # 实时读取输出并更新进度
        for line in iter(process.stdout.readline, ''):
            if not line:
                break

            # 检查任务是否被取消
            if job_id and JOB_STATUS.get(job_id, {}).get('status') == 'cancelled':
                logger.info(f"[Pipeline] 检测到任务取消请求，终止流水线进程: {job_id}")
                _kill_process_tree(process.pid)
                PROCESS_MAP.pop(job_id, None)
                return False

            # 输出到日志
            logger.info(f"[Pipeline] {line.rstrip()}")

            # 解析进度
            if job_id:
                progress_info = _parse_pipeline_progress(line)
                if progress_info:
                    step_name, progress = progress_info

                    # 步骤名称映射（中文显示）
                    step_display = {
                        'pipeline_start': '启动流水线',
                        'audio_separation': '音视频分离',
                        'audio_processing': '处理音频',
                        'transcription': '语音转录',
                        'diarization': '说话人识别',
                        'audio_separation_done': '音视频处理完成',
                        'translation': '字幕翻译',
                        'translating': '翻译处理中',
                        'translation_done': '翻译完成',
                        'tts_synthesis': 'TTS语音合成',
                        'tts_processing': 'TTS处理中',
                        'tts_generating': '生成配音',
                        'tts_done': 'TTS合成完成',
                        'merging_start': '开始合并',
                        'merging': '音视频合并',
                        'merging_done': '合并完成',
                        'final_video': '生成最终视频',
                        'completed': '流水线执行完成'
                    }.get(step_name, step_name)

                    # 更新任务状态
                    if job_id in JOB_STATUS:
                        JOB_STATUS[job_id].update({
                            'status': 'running',
                            'step': step_display,
                            'progress': progress,
                            'user_id': user_id,
                            'ts': time.time()
                        })
                        logger.info(f"[Progress] Job {job_id}: {step_display} ({progress}%)")

                        # 当翻译完成时，立即检查并返回字幕路径
                        if step_name == 'translation_done' and output_dir:
                            video_stem = video_path.stem
                            translated_srt = output_dir / f"{video_stem}.translated.srt"

                            if translated_srt.exists():
                                # 获取相对路径
                                try:
                                    translated_srt_rel = str(translated_srt.relative_to(PROJECT_ROOT))
                                except ValueError:
                                    translated_srt_rel = str(translated_srt.resolve())

                                # 更新 data 字段，包含字幕路径
                                if 'data' not in JOB_STATUS[job_id]:
                                    JOB_STATUS[job_id]['data'] = {}

                                JOB_STATUS[job_id]['data']['translated_srt'] = translated_srt_rel
                                logger.info(f"[Progress] 翻译后的字幕已就绪: {translated_srt_rel}")

        # 等待进程完成
        process.wait()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)

        # 处理后文件移动
        # full_auto_pipeline.py 会将输出保存到 output/<video_stem>/
        # 如果指定了 output_dir（命名空间目录），则需要移动文件
        if output_dir is not None:
            video_stem = video_path.stem
            default_output = Path('output') / video_stem

            if default_output.exists() and default_output != output_dir:
                logger.info(f"[流水线] 移动输出文件: {default_output} -> {output_dir}")
                output_dir.parent.mkdir(parents=True, exist_ok=True)

                # 如果目标目录已存在，先删除
                if output_dir.exists():
                    shutil.rmtree(output_dir)

                # 移动整个目录
                shutil.move(str(default_output), str(output_dir))
                logger.info(f"[流水线] 文件移动完成")

        # 标记任务为即将完成，避免前端停留在中间进度
        if job_id and job_id in JOB_STATUS:
            JOB_STATUS[job_id].update({
                'status': 'running',
                'step': '流水线执行完成',
                'progress': 98,
                'user_id': user_id,
                'ts': time.time()
            })
            logger.info(f"[Progress] Job {job_id}: 流水线执行完成 (98%)")

        logger.info(f"[Pipeline] 流水线成功完成，返回 True")

        # 清理 PROCESS_MAP
        if job_id:
            PROCESS_MAP.pop(job_id, None)

        return True

    except subprocess.CalledProcessError as e:
        # 构建详细的错误信息
        error_msg = f"流水线执行失败 (返回码: {e.returncode})"
        cmd_str = ' '.join(str(c) for c in e.cmd)
        error_details = f"命令: {cmd_str}\n返回码: {e.returncode}"

        logger.error(f"[Pipeline] 流水线执行失败: returncode={e.returncode}, cmd={e.cmd}", exc_info=True)
        logger.error(f"[Pipeline] 子进程命令: {cmd_str}")

        if hasattr(e, 'output') and e.output:
            logger.error(f"[Pipeline] 子进程输出: {e.output}")
            error_details += f"\n\n输出:\n{e.output}"
        if hasattr(e, 'stderr') and e.stderr:
            logger.error(f"[Pipeline] 子进程错误输出: {e.stderr}")
            error_details += f"\n\n错误输出:\n{e.stderr}"

        # 更新任务状态，包含详细错误信息
        if job_id and job_id in JOB_STATUS:
            JOB_STATUS[job_id].update({
                'pipeline_error': error_msg,
                'error_details': error_details
            })

        # 清理 PROCESS_MAP
        if job_id:
            PROCESS_MAP.pop(job_id, None)

        return False
    except Exception as e:
        error_msg = f"流水线执行异常: {str(e)}"
        logger.error(f"[Pipeline] 流水线异常: {e}", exc_info=True)

        # 更新任务状态，包含详细错误信息
        if job_id and job_id in JOB_STATUS:
            JOB_STATUS[job_id].update({
                'pipeline_error': error_msg,
                'error_details': str(e)
            })

        # 清理 PROCESS_MAP
        if job_id:
            PROCESS_MAP.pop(job_id, None)

        return False


def _collect_outputs_from_dir(out_dir: Path, stem: str) -> dict:
    """
    收集输出目录中的文件路径
    返回相对路径（相对于项目根目录），方便前端使用
    """
    data = {
        'output_dir': str(out_dir.resolve()),
        'initial_srt': None,
        'merged_srt': None,
        'translated_srt': None,
        'final_video': None,
    }
    initial_srt = out_dir / f"{stem}.srt"
    merged_srt = out_dir / f"{stem}_merged_optimized.srt"
    translated_srt = out_dir / f"{stem}.translated.srt"
    final_video = out_dir / 'merge' / f"{stem}_dubbed.mp4"

    # 转换为相对路径（相对于项目根目录）
    project_root = PROJECT_ROOT

    if initial_srt.exists():
        try:
            data['initial_srt'] = str(initial_srt.relative_to(project_root))
        except ValueError:
            data['initial_srt'] = str(initial_srt.resolve())

    if merged_srt.exists():
        try:
            data['merged_srt'] = str(merged_srt.relative_to(project_root))
        except ValueError:
            data['merged_srt'] = str(merged_srt.resolve())

    if translated_srt.exists():
        try:
            data['translated_srt'] = str(translated_srt.relative_to(project_root))
        except ValueError:
            data['translated_srt'] = str(translated_srt.resolve())

    if final_video.exists():
        try:
            # 返回相对于 output/ 目录的路径，不包含 output/ 前缀
            output_root = Path('output')
            data['final_video'] = str(final_video.relative_to(output_root))
        except ValueError:
            # 如果文件不在 output/ 目录下，使用相对于项目根目录的路径
            try:
                data['final_video'] = str(final_video.relative_to(project_root))
            except ValueError:
                data['final_video'] = str(final_video.resolve())

    return data


def _ffprobe_duration_seconds(path: Path) -> Optional[float]:
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=nw=1:nk=1', str(path)
        ], capture_output=True, text=True, encoding='utf-8', check=True)
        s = result.stdout.strip()
        return float(s) if s else None
    except Exception:
        return None


def get_audio_duration(audio_path: Path) -> float:
    """获取音频文件时长（秒）"""
    try:
        duration = _ffprobe_duration_seconds(audio_path)
        return float(duration) if duration is not None else 0.0
    except Exception:
        return 0.0


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get('/api/system/stats')
async def get_system_stats():
    """获取系统GPU和内存状态"""
    try:
        stats = _get_system_stats()
        return JSONResponse({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"[系统监控] 获取系统状态失败: {e}", exc_info=True)
        # 返回空数据而不是错误，前端可以静默处理
        return JSONResponse({
            'success': True,
            'data': {
                'gpu_available': False,
                'gpus': [],
                'system_memory': {
                    'total_gb': 0,
                    'used_gb': 0,
                    'available_gb': 0,
                    'percent': 0
                }
            }
        })


@app.get('/api/config')
async def get_config(request: Request):
    """获取用户配置"""
    try:
        from config_manager import get_config_manager

        # 获取用户ID，支持用户隔离
        user_id = _get_user_id(request)
        config_mgr = get_config_manager(user_id=user_id)

        return JSONResponse({
            'success': True,
            'data': config_mgr.get_all()
        })
    except Exception as e:
        logger.error(f"[配置读取] 失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/config')
async def update_config(request: Request):
    """更新用户配置"""
    try:
        from config_manager import get_config_manager

        # 解析请求数据
        data = await request.json()

        # 获取用户ID，支持用户隔离
        user_id = _get_user_id(request)
        config_mgr = get_config_manager(user_id=user_id)

        # 更新配置
        config_mgr.update(data)

        # 保存到文件
        success = config_mgr.save_config()

        if success:
            logger.info(f"[配置更新] 用户 {user_id} 成功保存配置")
            return JSONResponse({
                'success': True,
                'data': config_mgr.get_all()
            })
        else:
            return JSONResponse({
                'success': False,
                'error': '保存配置失败'
            }, status_code=500)

    except Exception as e:
        logger.error(f"[配置更新] 失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/config/reset')
async def reset_config(request: Request):
    """重置配置为默认值"""
    try:
        from config_manager import get_config_manager

        # 获取用户ID，支持用户隔离
        user_id = _get_user_id(request)
        config_mgr = get_config_manager(user_id=user_id)

        config_mgr.reset_to_default()
        config_mgr.save_config()

        logger.info(f"[配置重置] 用户 {user_id} 已重置为默认值")
        return JSONResponse({
            'success': True,
            'data': config_mgr.get_all()
        })
    except Exception as e:
        logger.error(f"[配置重置] 失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.get('/api/config/translation-models')
async def get_translation_models(api_type: Optional[str] = None):
    """获取可用的翻译模型列表

    Args:
        api_type: API类型（gemini 或 openai），如果不提供则返回所有

    Returns:
        翻译模型列表，包含模型ID、显示名称和推荐标记
    """
    try:
        # 定义可用的翻译模型
        models = {
            "gemini": [
                {
                    "id": "gemini-2.5-flash",
                    "name": "Gemini 2.5 Flash",
                    "description": "最新版本，速度快且质量高",
                    "recommended": True
                },
                {
                    "id": "gemini-2.5-pro",
                    "name": "Gemini 2.5 Pro",
                    "description": "最高质量，适合复杂翻译",
                    "recommended": False
                },
                {
                    "id": "gemini-2.0-flash-exp",
                    "name": "Gemini 2.0 Flash (实验版)",
                    "description": "实验版本，速度极快",
                    "recommended": False
                },
                {
                    "id": "gemini-2.0-flash-thinking-exp",
                    "name": "Gemini 2.0 Flash Thinking (实验版)",
                    "description": "具有推理能力，质量更高",
                    "recommended": False
                }
            ],
            "openai": [
                {
                    "id": "gpt-4o",
                    "name": "GPT-4o",
                    "description": "最新多模态模型，质量最高",
                    "recommended": True
                },
                {
                    "id": "gpt-4-turbo",
                    "name": "GPT-4 Turbo",
                    "description": "更快的GPT-4版本",
                    "recommended": False
                },
                {
                    "id": "gpt-4",
                    "name": "GPT-4",
                    "description": "高质量翻译",
                    "recommended": False
                },
                {
                    "id": "gpt-3.5-turbo",
                    "name": "GPT-3.5 Turbo",
                    "description": "快速且经济",
                    "recommended": False
                }
            ]
        }

        # 根据api_type筛选
        if api_type:
            api_type_lower = api_type.lower()
            if api_type_lower in models:
                result = {api_type_lower: models[api_type_lower]}
            else:
                return JSONResponse({
                    'success': False,
                    'error': f'不支持的API类型: {api_type}'
                }, status_code=400)
        else:
            result = models

        return JSONResponse({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"[获取翻译模型列表] 失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.get('/limits')
def get_limits():
    """获取当前的视频处理限制配置"""
    return {
        'max_video_minutes': MAX_VIDEO_MINUTES,
        'max_video_bytes': MAX_VIDEO_BYTES,
        'max_video_mb': round(MAX_VIDEO_BYTES / (1024 * 1024), 1)
    }


@app.get('/videos')
def get_user_videos(request: Request, user_id: Optional[str] = None):
    """获取用户的视频历史列表"""
    start_time = time.time()
    client_ip = request.client.host if request.client else 'unknown'
    
    try:
        # 获取用户ID
        if not user_id:
            user_id = _get_user_id(request)
        
        # 扫描output目录，查找该用户的视频
        output_dir = Path('output')
        if not output_dir.exists():
            logger.warning(f"[视频历史] output目录不存在: {output_dir}")
            return {'videos': []}
        
        videos = []
        total_projects = 0
        found_videos = 0
        
        # 遍历output目录下的所有子目录
        for user_dir in output_dir.iterdir():
            if not user_dir.is_dir():
                continue
                
            # 检查是否是该用户的目录
            if user_id and user_dir.name != user_id:
                continue
                
            # 遍历该用户目录下的所有项目
            for project_dir in user_dir.iterdir():
                if not project_dir.is_dir():
                    continue
                    
                total_projects += 1
                
                # 查找最终生成的视频文件 - 检查子目录中的merge目录
                final_video = None
                
                # 遍历项目目录下的所有子目录（如ZH_test）
                for subdir in project_dir.iterdir():
                    if subdir.is_dir():
                        # 检查子目录中的merge目录
                        merge_dir = subdir / "merge"
                        if merge_dir.exists() and merge_dir.is_dir():
                            for video_file in merge_dir.glob("*.mp4"):
                                if video_file.is_file():
                                    final_video = video_file
                                    break
                        if final_video:
                            break
                
                if final_video and final_video.exists():
                    # 获取文件信息
                    stat = final_video.stat()
                    file_size = stat.st_size
                    create_time = stat.st_ctime
                    
                    # 查找相关的SRT文件
                    srt_files = {
                        'original': None,
                        'translated': None,
                        'merged': None
                    }
                    
                    for srt_type, filename in [
                        ('original', f"{project_dir.name}.srt"),
                        ('translated', f"{project_dir.name}.translated.srt"),
                        ('merged', f"{project_dir.name}_merged_optimized.srt")
                    ]:
                        srt_path = project_dir / filename
                        if srt_path.exists():
                            srt_files[srt_type] = str(srt_path.relative_to(output_dir))
                    
                    videos.append({
                        'project_id': project_dir.name,
                        'user_id': user_dir.name,
                        'video_path': str(final_video.relative_to(output_dir)),
                        'video_size': file_size,
                        'create_time': create_time,
                        'srt_files': srt_files,
                        'project_dir': str(project_dir.relative_to(output_dir))
                    })
                    found_videos += 1
        
        # 按创建时间倒序排列
        videos.sort(key=lambda x: x['create_time'], reverse=True)
        
        processing_time = time.time() - start_time
        
        # 只在有视频或处理时间较长时才输出详细信息
        if found_videos > 0 or processing_time > 0.1:
            logger.info(f"[视频历史] 扫描完成 - 用户: {user_id}, 项目: {total_projects}, 视频: {found_videos}, 耗时: {processing_time:.2f}s")
        elif found_videos == 0 and total_projects > 0:
            # 只在第一次发现没有视频时输出警告
            logger.debug(f"[视频历史] 用户 {user_id} 暂无视频 - 项目数: {total_projects}")
        
        return {'videos': videos}
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"[视频历史] 获取失败 - 用户: {user_id}, 耗时: {processing_time:.2f}s, 错误: {e}")
        return {'error': str(e), 'videos': []}

@app.get('/video/{video_path:path}')
def download_video(video_path: str, request: Request):
    """下载指定的视频文件"""
    try:
        # 构建完整路径 - video_path可能已包含'output/'前缀
        # 先移除可能存在的'output/'前缀，然后统一拼接
        clean_path = video_path.removeprefix('output/').removeprefix('output\\')
        full_path = Path('output') / clean_path

        # 安全检查：确保文件在output目录内
        if not str(full_path.resolve()).startswith(str(Path('output').resolve())):
            logger.warning(f"[视频下载] 无效路径: {video_path}")
            return {'error': 'Invalid file path'}

        if not full_path.exists():
            logger.warning(f"[视频下载] 文件不存在: {clean_path} -> {full_path}")
            return {'error': 'File not found'}
        
        # 获取文件信息
        stat = full_path.stat()
        file_size = stat.st_size
        logger.info(f"[视频下载] 下载: {full_path.name} ({file_size} bytes)")
        
        # 返回文件
        from fastapi.responses import FileResponse
        return FileResponse(
            path=str(full_path),
            filename=full_path.name,
            media_type='video/mp4'
        )
        
    except Exception as e:
        logger.error(f"[视频下载] 失败: {video_path} - {e}")
        return {'error': str(e)}

@app.delete('/video/{video_path:path}')
def delete_video(video_path: str, request: Request):
    """删除指定的视频项目"""
    try:
        # 构建完整路径
        full_path = Path('output') / video_path
        
        # 安全检查：确保路径在output目录内
        if not str(full_path.resolve()).startswith(str(Path('output').resolve())):
            logger.warning(f"[视频删除] 无效路径: {video_path}")
            return {'error': 'Invalid file path'}
        
        if not full_path.exists():
            logger.warning(f"[视频删除] 文件不存在: {video_path}")
            return {'error': 'File not found'}
        
        # 获取项目目录信息
        project_dir = full_path.parent
        project_size = sum(f.stat().st_size for f in project_dir.rglob('*') if f.is_file())
        
        logger.info(f"[视频删除] 删除项目: {project_dir.name} ({project_size} bytes)")
        
        # 删除整个项目目录
        import shutil
        shutil.rmtree(project_dir)
        
        return {'message': 'Video project deleted successfully'}
        
    except Exception as e:
        logger.error(f"[视频删除] 失败: {video_path} - {e}")
        return {'error': str(e)}


@app.get('/srt')
def get_translated_srt(stem: str, user_id: Optional[str] = None, job_id: Optional[str] = None):
    """返回 output/<stem>/<stem>.translated.srt 内容。"""
    out_dir = _resolve_out_dir(stem, user_id=user_id, job_id=job_id)
    legacy_dir = Path('output') / stem
    # 仅查找，不再进行命名空间与 legacy 之间的同步复制
    if out_dir is not None:
        srt_path = out_dir / f"{stem}.translated.srt"
        if not srt_path.exists():
            # 回退 legacy 读取
            legacy_srt = legacy_dir / f"{stem}.translated.srt"
            if not legacy_srt.exists():
                return JSONResponse({'error': f'未找到翻译SRT'}, status_code=404)
            srt_path = legacy_srt
    else:
        legacy_srt = legacy_dir / f"{stem}.translated.srt"
        if not legacy_srt.exists():
            return JSONResponse({'error': f'未找到翻译SRT'}, status_code=404)
        srt_path = legacy_srt
    try:
        content = srt_path.read_text(encoding='utf-8', errors='ignore')
        return JSONResponse({'stem': stem, 'path': str(srt_path.resolve()), 'content': content})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@app.post('/srt/save')
async def save_translated_srt(stem: str = Form(...), content: str = Form(...), user_id: Optional[str] = Form(default=None), job_id: Optional[str] = Form(default=None)):
    # 严格：若提供 user/job，则仅写入命名空间；否则写入 legacy
    out_dir = None
    if user_id and job_id:
        out_dir = Path('output') / user_id / job_id / stem
    else:
        # 回退 legacy
        out_dir = Path('output') / stem
    srt_path = out_dir / f"{stem}.translated.srt"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        srt_path.write_text(content, encoding='utf-8')
        return JSONResponse({'status': 'saved', 'path': str(srt_path.resolve())})
    except Exception as e:
        return JSONResponse({'status': 'failed', 'error': str(e)}, status_code=500)


@app.post('/continue_tts')
async def continue_tts(
    stem: str = Form(...),
    user_id: Optional[str] = Form(default=None),
    job_id: Optional[str] = Form(default=None),
    tts_engine: str = Form('indextts'),
    text_lang: str = Form('auto'),
    prompt_lang: str = Form('auto'),
    source_lang: Optional[str] = Form(default=None),
    speed_factor: Optional[float] = Form(None),
    resume: bool = Form(True),
):
    """基于已生成的输出（含 translated.srt），继续执行 TTS 与合并。"""
    try:
        out_dir = _resolve_out_dir(stem, user_id=user_id, job_id=job_id)
        if out_dir is None:
            return JSONResponse({'error': f'未找到输出目录: {stem}'}, status_code=404)
        translated_srt = out_dir / f"{stem}.translated.srt"
        merged_srt = out_dir / f"{stem}_merged_optimized.srt"
        speak_wav = out_dir / f"{stem}_speak.wav"
        if not (translated_srt.exists() and merged_srt.exists() and speak_wav.exists()):
            return JSONResponse({'error': '缺少必要文件，请先完成转写和翻译'}, status_code=400)

        # 已禁用legacy同步：避免 output/<stem> 被写入，强制使用命名空间目录
        # legacy_dir = Path('output') / stem
        # try:
        #     legacy_dir.mkdir(parents=True, exist_ok=True)
        #     for p in [translated_srt, merged_srt, speak_wav]:
        #         dest = legacy_dir / p.name
        #         if p.exists():
        #             try:
        #                 if not dest.exists() or p.stat().st_mtime > dest.stat().st_mtime:
        #                     shutil.copy2(p, dest)
        #             except Exception:
        #                 pass
        # except Exception as e:
        #     logger.warning(f"同步兼容文件至 legacy 输出失败: {e}")

        run_env = os.environ.copy()
        run_env['PYTHONIOENCODING'] = 'utf-8'
        run_env['PYTHONUTF8'] = '1'

        logger.info(f"continue_tts langs | text_lang={text_lang} prompt_lang_in={prompt_lang} source_lang={source_lang}")

        if tts_engine.lower() in ['indextts', 'indextts2', 'indextts2']:
            cmd = [
                sys.executable, 'stepB_index_pipeline.py', stem,
                '-o', str(out_dir),
            ]
            if resume:
                cmd.append('--resume')
            subprocess.run(cmd, check=True, env=run_env)
        else:
            # gpt-sovits
            # prompt_lang=auto 在 generate_gptsovits_batch 中不被接受，优先用 source_lang，其次用 text_lang
            src = (source_lang or '').lower()
            eff_prompt_lang = prompt_lang
            if str(prompt_lang).lower() == 'auto':
                if src in ['zh','en','ja','ko','chinese','english','japanese','korean'] and src != 'auto':
                    eff_prompt_lang = source_lang
                else:
                    eff_prompt_lang = text_lang
            cmd = [
                sys.executable, 'stepB_gptsovits_pipeline.py', stem,
                '-o', str(out_dir),
                '--mode', 'local', '--text_lang', text_lang, '--prompt_lang', eff_prompt_lang
            ]
            logger.info(f"continue_tts gsv params | text_lang={text_lang} prompt_lang={eff_prompt_lang}")
            if resume:
                cmd.append('--resume')
            if speed_factor is not None:
                cmd.extend(['--speed_factor', str(speed_factor)])
            subprocess.run(cmd, check=True, env=run_env)

        # 汇总结果
        final_video = out_dir / 'merge' / f"{stem}_dubbed.mp4"
        tts_dir_ind = out_dir / 'tts'
        tts_dir_gsv = out_dir / 'tts_gptsovits'
        return JSONResponse({
            'status': 'success',
            'final_video': str(final_video.resolve()) if final_video.exists() else None,
            'tts_dir': str((tts_dir_gsv if tts_dir_gsv.exists() else tts_dir_ind).resolve())
        })
    except subprocess.CalledProcessError as e:
        return JSONResponse({'status': 'failed', 'error': str(e)}, status_code=500)
    except Exception as e:
        return JSONResponse({'status': 'failed', 'error': str(e)}, status_code=500)

# 定义 Pipeline 配置模型（前端API）
class PipelineStartRequest(BaseModel):
    videoFile: str
    outputDir: str
    translation: dict  # {sourceLanguage, targetLanguage}
    tts: dict  # {engine}
    subtitle: Optional[dict] = None  # {mode, language, ...}
    skipSteps: Optional[list] = None


@app.post('/api/pipeline/start')
async def start_pipeline_api(request: Request, config: PipelineStartRequest):
    """
    前端流水线启动API - 接收 PipelineConfig 并返回 TaskResponse
    """
    try:
        logger.info(f"[流水线启动] 收到请求: {config.model_dump()}")

        # 解析配置
        video_path = config.videoFile
        source_lang = config.translation.get('sourceLanguage', 'en')
        target_lang = config.translation.get('targetLanguage', 'zh')
        tts_engine = config.tts.get('engine', 'indextts')

        # 映射语言代码（前端使用完整名称，后端使用两字母代码）
        lang_map = {'english': 'en', 'chinese': 'zh', 'japanese': 'ja', 'korean': 'ko'}
        source_lang = lang_map.get(source_lang.lower(), source_lang)
        target_lang = lang_map.get(target_lang.lower(), target_lang)

        # 检查视频文件是否存在
        video = Path(video_path)
        if not video.exists():
            logger.warning(f"[流水��启动] 视频文件不存在: {video_path}")
            return JSONResponse({
                'success': False,
                'error': f'视频文件不存在: {video_path}'
            }, status_code=400)

        # 获取用户ID
        user_id = _get_user_id(request)

        # 检查是否已有活动任务
        existing = _user_has_active_job(user_id)
        if existing:
            logger.warning(f"[流水线启动] 用户已有活动任务: {existing}")
            return JSONResponse({
                'success': False,
                'error': '您已有正在运行的任务，请等待完成后再提交新任务',
                'activeJobId': existing
            }, status_code=409)

        # 生成任务ID
        job_id = _new_job_id()

        # 创建任务对象
        job = {
            'job_id': job_id,
            'user_id': user_id,
            'video': str(video.resolve()),
            'skip_tts': False,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'transcribe_engine': 'whisperx',
            'tts_engine': tts_engine,
            'diarization': True,
            'separation': True,
            'speed_factor': None,
        }

        # 添加到任务队列
        JOB_STATUS[job_id] = {'status': 'queued', 'progress': 0, 'user_id': user_id, 'ts': time.time()}
        JOB_QUEUE.append(job)

        logger.info(f"[流水线启动] 任务已加入队列: {job_id}")

        # 返回标准的 TaskResponse
        return JSONResponse({
            'success': True,
            'data': {
                'taskId': job_id,
                'status': 'queued',
                'message': '任务已加入队列，正在等待处理'
            }
        })

    except Exception as e:
        logger.error(f"[流水线启动] 失败: {e}", exc_info=True)
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/process')
async def process(
    request: Request,
    file: Optional[UploadFile] = File(default=None),
    video_path: Optional[str] = Form(default=None),
    source_lang: str = Form(default='auto'),
    target_lang: str = Form(...),
    tts_engine: str = Form(default='indextts'),  # indextts / gptsovits
    transcribe_engine: str = Form(default='whisperx'),  # whisperx only
    diarization: Optional[bool] = Form(default=True),
    separation: Optional[bool] = Form(default=True),
    speed_factor: Optional[float] = Form(default=None),
    skip_tts: Optional[bool] = Form(default=False),
):
    """
    提交任务：可上传文件或提供本地路径。
    成功后返回关键输出文件路径。
    """
    try:
        logger.info(f"/process called from {request.client.host if request.client else 'unknown'} | params: target_lang={target_lang}, tts_engine={tts_engine}, transcribe_engine={transcribe_engine}, source_lang={source_lang}, diarization={diarization}, separation={separation}, speed_factor={speed_factor}, skip_tts={skip_tts}")

        if file is None and not video_path:
            return JSONResponse({'error': '必须提供上传文件(file)或本地路径(video_path)。'}, status_code=400)

        # 用户与作业ID
        user_id = _get_user_id(request)
        # 同一用户限制：如已有活动任务则直接返回冲突
        existing = _user_has_active_job(user_id)
        if existing:
            return JSONResponse({'error': '同一用户仅允许单任务执行', 'active_job_id': existing}, status_code=409)
        job_id = _new_job_id()

        # 准备输入视频（保存到 input/<user>/<job>/）
        if file is not None:
            in_dir = Path('input') / user_id / job_id
            in_dir.mkdir(parents=True, exist_ok=True)
            save_path = in_dir / file.filename
            with open(save_path, 'wb') as f:
                shutil.copyfileobj(file.file, f)
            video = save_path
        else:
            video = Path(video_path).resolve()
            if not video.exists():
                return JSONResponse({'error': f'输入视频不存在: {video}'}, status_code=400)

        # 文件大小限制
        try:
            size_bytes = video.stat().st_size
            if size_bytes > MAX_VIDEO_BYTES:
                size_mb = size_bytes / (1024 * 1024)
                max_mb = MAX_VIDEO_BYTES / (1024 * 1024)
                return JSONResponse({
                    'error': f'视频文件过大！当前文件: {size_mb:.1f}MB，最大限制: {max_mb:.1f}MB',
                    'file_size': size_mb,
                    'max_size': max_mb,
                    'suggestion': '请压缩视频或选择较小的文件'
                }, status_code=400)
        except Exception:
            pass

        # 时长限制（需要 ffprobe）
        duration = _ffprobe_duration_seconds(video)
        if duration is not None and duration > MAX_VIDEO_MINUTES * 60:
            duration_minutes = duration / 60
            return JSONResponse({
                'error': f'视频时长过长！当前时长: {duration_minutes:.1f}分钟，最大限制: {MAX_VIDEO_MINUTES}分钟',
                'duration': duration_minutes,
                'max_duration': MAX_VIDEO_MINUTES,
                'suggestion': '请裁剪视频或选择较短的片段'
            }, status_code=400)

        # 校验参数兼容性
        if tts_engine == 'indextts' and target_lang not in ['zh', 'en']:
            return JSONResponse({'error': 'indextts 仅支持目标语言 zh/en'}, status_code=400)
        if tts_engine == 'gptsovits' and target_lang not in ['zh', 'en', 'ja', 'ko']:
            return JSONResponse({'error': 'gpt-sovits 仅支持目标语言 zh/en/ja/ko'}, status_code=400)

        # 执行：使用单实例信号量，防止并发阻塞，放到线程池运行
        tts_engine_norm = ('gptsovits' if tts_engine.lower() == 'gpt-sovits' else tts_engine)

        async def _do_job():
            async with _EXEC_SEMA:
                global CURRENT_RUNNING
                CURRENT_RUNNING = job_id
                JOB_STATUS[job_id] = {'status': 'running', 'step': 'start', 'progress': 0}
                if skip_tts:
                    logger.info("Skip TTS mode: run stepA + translate only")
                    out_dir_tmp = Path('output') / video.stem
                    out_dir_tmp.mkdir(parents=True, exist_ok=True)
                    # stepA
                    cmd_a = [
                        sys.executable, 'stepA_prepare_and_blank_srt.py',
                        str(video), '-o', str(out_dir_tmp), '-e', transcribe_engine,
                    ]
                    if str(source_lang).lower() == 'auto':
                        cmd_a.extend(['-l', 'auto'])
                    if not diarization:
                        cmd_a.append('--no-diarize')
                    if not separation:
                        cmd_a.append('--no-separation')
                    JOB_STATUS[job_id] = {'status': 'running', 'step': 'stepA', 'progress': 20}
                    await asyncio.get_event_loop().run_in_executor(None, lambda: subprocess.run(cmd_a, check=True))
                    # translate (whole)
                    srt_file = out_dir_tmp / f"{video.stem}.srt"
                    translated_srt = out_dir_tmp / f"{video.stem}.translated.srt"
                    cmd_t = [
                        sys.executable, 'Scripts/step4_translate_srt.py',
                        str(srt_file), '--target_lang', target_lang, '--whole_file',
                        '-o', str(translated_srt)
                    ]
                    JOB_STATUS[job_id] = {'status': 'running', 'step': 'translate', 'progress': 60}
                    await asyncio.get_event_loop().run_in_executor(None, lambda: subprocess.run(cmd_t, check=True))
                    JOB_STATUS[job_id] = {'status': 'running', 'step': 'finalize', 'progress': 80}
                    return out_dir_tmp
                else:
                    logger.info(f"Start pipeline: video={video} tts={tts_engine_norm} transcriber={transcribe_engine} src={source_lang} tgt={target_lang} dia={diarization} sep={separation} speed={speed_factor}")
                    JOB_STATUS[job_id] = {'status': 'running', 'step': 'full_pipeline', 'progress': 10}
                    await asyncio.get_event_loop().run_in_executor(None, lambda: _run_full_pipeline(
                        video_path=video,
                        target_lang=target_lang,
                        transcribe_engine=transcribe_engine,
                        source_lang=source_lang,
                        tts_engine=tts_engine_norm,
                        diarization=bool(diarization),
                        separation=bool(separation),
                        speed_factor=speed_factor,
                    ))
                    JOB_STATUS[job_id] = {'status': 'running', 'step': 'finalize', 'progress': 90}
                    return Path('output') / video.stem

        # 入队任务（每位用户只能中断自己的任务）
        job = {
            'job_id': job_id,
            'user_id': user_id,
            'video': str(video),
            'skip_tts': bool(skip_tts),
            'source_lang': source_lang,
            'target_lang': target_lang,
            'transcribe_engine': transcribe_engine,
            'tts_engine': tts_engine_norm,
            'diarization': bool(diarization),
            'separation': bool(separation),
            'speed_factor': speed_factor,
        }
        JOB_STATUS[job_id] = {'status': 'queued', 'progress': 0, 'user_id': user_id, 'ts': time.time()}
        JOB_QUEUE.append(job)

        # 收集输出
        # 立即返回队列信息（异步执行，前端通过 /progress 轮询）
        data = {
            'user_id': user_id,
            'job_id': job_id,
            'video_stem': _stem_from_path(video),
            'queued': True
        }
        return JSONResponse({'status': 'queued', 'data': data})

    except subprocess.CalledProcessError as e:
        logger.error(f"Pipeline failed (subprocess): {e}")
        return JSONResponse({'status': 'failed', 'error': str(e)}, status_code=500)
    except Exception as e:
        logger.error(f"Pipeline failed (exception): {e}")
        return JSONResponse({'status': 'failed', 'error': str(e)}, status_code=500)


# ==================== 前端工具API ====================

# 工具任务字典（独立于主流水线）
TOOL_TASKS: dict = {}

# 请求模型定义
class VideoDownloadRequest(BaseModel):
    url: str
    quality: str = '1080p'
    audioOnly: bool = False

class TranscribeRequest(BaseModel):
    language: Optional[str] = None
    model: str = 'large-v3'
    enableDiarization: bool = True

@app.post('/api/upload/video')
async def upload_video_api(request: Request, file: UploadFile = File(...)):
    """
    视频上传API - 仅上传文件，不进行处理
    返回文件信息供后续处理使用
    """
    try:
        user_id = _get_user_id(request)
        job_id = _new_job_id()

        logger.info(f"[视频上传] 用户: {user_id}, 任务: {job_id}, 文件: {file.filename}")

        # 创建输入目录
        in_dir = Path('input') / user_id / job_id
        in_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        file_path = in_dir / file.filename
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # 获取文件信息
        file_size = file_path.stat().st_size
        file_id = f"{user_id}_{job_id}"

        logger.info(f"[视频上传] 上传成功: {file_path} ({file_size} bytes)")

        return JSONResponse({
            'success': True,
            'data': {
                'fileId': file_id,
                'fileName': file.filename,
                'fileSize': file_size,
                'filePath': str(file_path.resolve()),
                'userId': user_id,
                'jobId': job_id
            }
        })

    except Exception as e:
        logger.error(f"[视频上传] 失败: {e}", exc_info=True)
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.get('/api/videos/preview/{video_id}')
async def preview_video(video_id: str):
    """
    视频预览API - 根据video_id返回视频文件供前端播放
    video_id 格式: user_id_job_id
    """
    try:
        # 解析 video_id
        parts = video_id.split('_', 1)
        if len(parts) != 2:
            logger.warning(f"[视频预览] 无效的 video_id 格式: {video_id}")
            return JSONResponse({
                'error': 'Invalid video_id format'
            }, status_code=400)

        user_id, job_id = parts

        # 查找视频文件
        in_dir = Path('input') / user_id / job_id

        if not in_dir.exists():
            logger.warning(f"[视频预览] 目录不存在: {in_dir}")
            return JSONResponse({
                'error': 'Video not found'
            }, status_code=404)

        # 查找目录中的视频文件（支持常见视频格式）
        video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.m4v']
        video_file = None

        for file_path in in_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                video_file = file_path
                break

        if not video_file or not video_file.exists():
            logger.warning(f"[视频预览] 未找到视频文件: {in_dir}")
            return JSONResponse({
                'error': 'Video file not found in directory'
            }, status_code=404)

        # 安全检查：确保文件在 input 目录内
        if not str(video_file.resolve()).startswith(str(Path('input').resolve())):
            logger.error(f"[视频预览] 安全检查失败: {video_file}")
            return JSONResponse({
                'error': 'Invalid file path'
            }, status_code=403)

        logger.info(f"[视频预览] 播放视频: {video_file} ({video_file.stat().st_size} bytes)")

        # 返回视频文件
        return FileResponse(
            path=str(video_file.resolve()),
            media_type='video/mp4',
            filename=video_file.name
        )

    except Exception as e:
        logger.error(f"[视频预览] 失败: {e}", exc_info=True)
        return JSONResponse({
            'error': str(e)
        }, status_code=500)


@app.get('/api/subtitle/{subtitle_path:path}')
async def get_subtitle(subtitle_path: str):
    """
    读取字幕文件内容
    subtitle_path: 字幕文件相对路径 (例如: output/test/test.translated.srt)
    """
    try:
        # 构建完整路径
        file_path = Path(subtitle_path)

        # 安全检查：确保文件路径在允许的目录内
        allowed_dirs = ['output', 'input']
        path_parts = file_path.parts

        if not path_parts or path_parts[0] not in allowed_dirs:
            logger.warning(f"[字幕读取] 非法路径: {subtitle_path}")
            return JSONResponse({
                'error': 'Invalid subtitle path'
            }, status_code=403)

        # 检查文件是否存在
        if not file_path.exists():
            logger.warning(f"[字幕读取] 文件不存在: {file_path}")
            return JSONResponse({
                'error': 'Subtitle file not found'
            }, status_code=404)

        # 检查是否是 .srt 文件
        if file_path.suffix.lower() not in ['.srt', '.vtt', '.ass', '.ssa']:
            logger.warning(f"[字幕读取] 非法文件类型: {file_path}")
            return JSONResponse({
                'error': 'Invalid subtitle file type'
            }, status_code=400)

        # 读取文件内容
        logger.info(f"[字幕读取] 读取文件: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return Response(
            content=content,
            media_type='text/plain; charset=utf-8'
        )

    except Exception as e:
        logger.error(f"[字幕读取] 失败: {e}", exc_info=True)
        return JSONResponse({
            'error': str(e)
        }, status_code=500)


@app.post('/api/download/video')
async def download_video_api(request: VideoDownloadRequest):
    """
    视频下载工具API
    """
    try:
        import yt_dlp
        
        url = request.url
        quality = request.quality
        audio_only = request.audioOnly
        
        user_id = 'web_user'
        job_id = str(uuid.uuid4())[:8]
        
        # 创建输出目录
        output_dir = Path('output') / f'download_{job_id}'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 异步执行下载
        async def download_task():
            try:
                logger.info(f"[下载任务] 开始下载: {url}")
                logger.info(f"[下载任务] 质量: {quality}, 仅音频: {audio_only}")
                
                if audio_only:
                    # 仅下载音频
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '320',
                        }],
                        'verbose': True,
                    }
                else:
                    # 下载视频
                    ydl_opts = {
                        'format': f'bestvideo[height<={quality[:-1]}]+bestaudio/best' if quality != 'best' else 'bestvideo+bestaudio/best',
                        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
                        'merge_output_format': 'mp4',
                        'verbose': True,
                    }
                
                logger.info(f"[下载任务] yt-dlp 选项: {ydl_opts}")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    
                    # 如果是音频，文件名会改变
                    if audio_only:
                        filename = filename.rsplit('.', 1)[0] + '.mp3'
                    
                    logger.info(f"[下载任务] 下载完成: {filename}")
                    
                    # 更新任务状态
                    if job_id in TOOL_TASKS:
                        TOOL_TASKS[job_id]['status'] = 'completed'
                        TOOL_TASKS[job_id]['progress'] = 100
                        TOOL_TASKS[job_id]['result'] = {
                            'filePath': filename,
                            'fileName': Path(filename).name,
                            'fileSize': Path(filename).stat().st_size if Path(filename).exists() else 0
                        }
                        logger.info(f"[下载任务] 任务完成: {job_id}")
            except Exception as e:
                logger.error(f"[下载任务] 下载失败: {e}", exc_info=True)
                if job_id in TOOL_TASKS:
                    TOOL_TASKS[job_id]['status'] = 'error'
                    TOOL_TASKS[job_id]['message'] = str(e)
        
        # 创建任务记录
        TOOL_TASKS[job_id] = {
            'user_id': user_id,
            'status': 'processing',
            'progress': 0,
            'message': f'下载视频: {url}',
            'result': None
        }
        
        # 启动异步任务
        asyncio.create_task(download_task())
        
        return JSONResponse({
            'success': True,
            'data': {
                'taskId': job_id,
                'status': 'processing',
                'message': '开始下载视频'
            }
        })
    
    except ImportError:
        return JSONResponse({
            'success': False,
            'error': 'yt-dlp 未安装，请运行: pip install yt-dlp'
        }, status_code=500)
    except Exception as e:
        logger.error(f"Download video failed: {e}")
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@app.get('/api/download/{taskId}')
async def get_download_status(taskId: str):
    """
    获取下载状态
    """
    if taskId in TOOL_TASKS:
        job = TOOL_TASKS[taskId]
        return JSONResponse({
            'success': True,
            'data': {
                'status': job['status'],
                'progress': job.get('progress', 0),
                'message': job.get('message', ''),
                'result': job.get('result')
            }
        })
    else:
        return JSONResponse({'success': False, 'error': 'Task not found'}, status_code=404)


@app.post('/api/tools/transcribe')
async def transcribe_tool(
    file: UploadFile = File(...),
    language: str = Form('auto'),
    model: str = Form('large-v3'),
    enableDiarization: str = Form('true'),
    beamSize: int = Form(5),
    temperature: float = Form(0.0),
    vadThreshold: float = Form(0.5),
    minSpeakers: int = Form(1),
    maxSpeakers: int = Form(5)
):
    """
    语音转录工具API（支持高级参数）

    Args:
        file: 上传的音频/视频文件
        language: 语言代码（auto/zh/en/ja/ko等）
        model: WhisperX模型（tiny/base/small/medium/large-v2/large-v3）
        enableDiarization: 是否启用说话人识别（'true'/'false'）
        beamSize: 束搜索大小（1-10）
        temperature: 采样温度（0.0-1.0）
        vadThreshold: VAD阈值（0.0-1.0）
        minSpeakers: 最少说话人数（1-10）
        maxSpeakers: 最多说话人数（1-10）
    """
    try:
        user_id = 'web_user'
        job_id = str(uuid.uuid4())[:8]

        # 保存上传的文件
        upload_dir = Path('output') / f'transcribe_{job_id}'
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / file.filename
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # 转换说话人识别参数
        diarize_enabled = enableDiarization.lower() == 'true'

        # 异步执行转录
        async def transcribe_task():
            try:
                logger.info(f"[转录任务] 开始转录: {file.filename}")
                logger.info(f"[转录任务] 文件路径: {file_path}")
                logger.info(f"[转录任务] 参数: language={language}, model={model}, diarize={diarize_enabled}")
                logger.info(f"[转录任务] 高级参数: beam_size={beamSize}, temp={temperature}, vad={vadThreshold}")
                if diarize_enabled:
                    logger.info(f"[转录任务] 说话人数量: {minSpeakers}-{maxSpeakers}")

                # 调用 WhisperX 转录（带高级参数）
                cmd = [
                    sys.executable,
                    'Scripts/step3_transcribe_whisperx.py',
                    str(file_path),
                    '-o', str(upload_dir / f'{file_path.stem}.srt'),
                    '-l', language,
                    '-m', model,
                    '--beam-size', str(beamSize),
                    '--temperature', str(temperature),
                    '--vad-threshold', str(vadThreshold)
                ]

                # 添加说话人识别参数
                if not diarize_enabled:
                    cmd.append('--no-diarize')
                else:
                    cmd.extend(['--min-speakers', str(minSpeakers)])
                    cmd.extend(['--max-speakers', str(maxSpeakers)])
                
                logger.info(f"[转录任务] 执行命令: {' '.join(cmd)}")
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                stdout, stderr = process.communicate()
                
                # 打印所有输出
                if stdout:
                    logger.info(f"[转录任务] 标准输出:\n{stdout}")
                if stderr:
                    logger.warning(f"[转录任务] 标准错误:\n{stderr}")
                
                logger.info(f"[转录任务] 进程返回码: {process.returncode}")
                
                if process.returncode == 0:
                    # 查找生成的SRT文件（可能有.srt.srt的问题）
                    possible_srt_files = [
                        upload_dir / f'{file_path.stem}.srt',
                        upload_dir / f'{file_path.stem}.srt.srt',
                    ]
                    
                    # 也在输出目录查找所有srt文件
                    srt_files = list(upload_dir.glob('*.srt'))
                    logger.info(f"[转录任务] 在 {upload_dir} 查找SRT文件...")
                    for f in srt_files:
                        logger.info(f"[转录任务] 发现SRT: {f}")
                    
                    srt_file = None
                    for p in possible_srt_files:
                        if p.exists():
                            srt_file = p
                            break
                    
                    # 如果还没找到，使用找到的第一个srt文件
                    if not srt_file and srt_files:
                        srt_file = srt_files[0]
                    
                    if srt_file:
                        TOOL_TASKS[job_id]['status'] = 'completed'
                        TOOL_TASKS[job_id]['progress'] = 100
                        TOOL_TASKS[job_id]['result'] = str(srt_file)
                        logger.info(f"[转录任务] 转录成功: {srt_file}")
                    else:
                        TOOL_TASKS[job_id]['status'] = 'error'
                        TOOL_TASKS[job_id]['message'] = 'SRT file not generated'
                        logger.error(f"[转录任务] SRT文件未生成")
                else:
                    error_msg = stderr or stdout or 'Transcription failed'
                    TOOL_TASKS[job_id]['status'] = 'error'
                    TOOL_TASKS[job_id]['message'] = error_msg
                    logger.error(f"[转录任务] 转录失败: {error_msg}")
                    
            except Exception as e:
                logger.error(f"[转录任务] 异常: {e}", exc_info=True)
                if job_id in TOOL_TASKS:
                    TOOL_TASKS[job_id]['status'] = 'error'
                    TOOL_TASKS[job_id]['message'] = str(e)
        
        # 创建任务记录
        TOOL_TASKS[job_id] = {
            'user_id': user_id,
            'status': 'processing',
            'progress': 0,
            'message': f'转录中: {file.filename}',
            'result': None
        }
        
        # 启动异步任务
        asyncio.create_task(transcribe_task())
        
        return JSONResponse({
            'success': True,
            'data': {
                'taskId': job_id,
                'status': 'processing',
                'message': '开始转录'
            }
        })
        
    except Exception as e:
        logger.error(f"Transcribe upload failed: {e}")
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@app.post('/api/tools/separate-audio')
async def separate_audio_tool(file: UploadFile = File(...)):
    """
    音频分离工具API
    """
    try:
        user_id = 'web_user'
        job_id = str(uuid.uuid4())[:8]
        
        # 保存上传的文件
        upload_dir = Path('output') / f'separate_{job_id}'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # 异步执行分离
        async def separate_task():
            try:
                logger.info(f"[分离任务] 开始分离: {file.filename}")
                logger.info(f"[分离任务] 文件路径: {file_path}")
                
                # 如果是视频，先分离视频音频
                if file.filename.endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm')):
                    logger.info(f"[分离任务] 检测到视频文件，先提取音频")
                    video_only = upload_dir / f'{file_path.stem}_video_only.mp4'
                    audio_file = upload_dir / f'{file_path.stem}_audio.wav'
                    
                    # 分离音频
                    cmd_audio = [
                        'ffmpeg', '-i', str(file_path),
                        '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
                        str(audio_file), '-y'
                    ]
                    logger.info(f"[分离任务] 提取音频命令: {' '.join(cmd_audio)}")
                    result_audio = subprocess.run(cmd_audio, capture_output=True, text=True, encoding='utf-8', errors='replace')
                    if result_audio.stdout:
                        logger.info(f"[分离任务] FFmpeg输出: {result_audio.stdout}")
                    if result_audio.stderr:
                        logger.warning(f"[分离任务] FFmpeg错误: {result_audio.stderr}")
                    
                    # 保存无声视频
                    cmd_video = [
                        'ffmpeg', '-i', str(file_path),
                        '-an', '-c:v', 'copy',
                        str(video_only), '-y'
                    ]
                    logger.info(f"[分离任务] 提取视频命令: {' '.join(cmd_video)}")
                    result_video = subprocess.run(cmd_video, capture_output=True, text=True, encoding='utf-8', errors='replace')
                    if result_video.stderr:
                        logger.warning(f"[分离任务] FFmpeg错误: {result_video.stderr}")
                else:
                    logger.info(f"[分离任务] 检测到音频文件")
                    audio_file = file_path
                    video_only = None
                
                # 分离人声和背景
                cmd_separate = [
                    sys.executable,
                    'Scripts/step2_separate_vocals.py',
                    str(audio_file)
                ]
                
                logger.info(f"[分离任务] 分离命令: {' '.join(cmd_separate)}")
                result_sep = subprocess.run(cmd_separate, capture_output=True, text=True, encoding='utf-8', errors='replace')
                
                if result_sep.stdout:
                    logger.info(f"[分离任务] 分离输出: {result_sep.stdout}")
                if result_sep.stderr:
                    logger.warning(f"[分离任务] 分离错误: {result_sep.stderr}")
                
                logger.info(f"[分离任务] 分离返回码: {result_sep.returncode}")
                
                # 查找生成的文件（可能在不同位置）
                # step2_separate_vocals.py 可能在源文件目录生成，也可能在当前目录
                possible_names = [
                    upload_dir / f'{audio_file.stem}_vocals.wav',
                    upload_dir / f'{file_path.stem}_vocals.wav',
                    Path(f'{audio_file}_vocals.wav'),
                    Path(f'{file_path.stem}_vocals.wav'),
                ]
                
                vocals_file = None
                for p in possible_names:
                    if p.exists():
                        vocals_file = p
                        logger.info(f"[分离任务] 找到人声文件: {vocals_file}")
                        break
                
                possible_inst_names = [
                    upload_dir / f'{audio_file.stem}_instrumental.wav',
                    upload_dir / f'{file_path.stem}_instrumental.wav',
                    Path(f'{audio_file}_instrumental.wav'),
                    Path(f'{file_path.stem}_instrumental.wav'),
                ]
                
                instrumental_file = None
                for p in possible_inst_names:
                    if p.exists():
                        instrumental_file = p
                        logger.info(f"[分离任务] 找到背景音乐: {instrumental_file}")
                        break
                
                if not vocals_file and not instrumental_file:
                    # 尝试在输出目录查找所有wav文件
                    logger.info(f"[分离任务] 在 {upload_dir} 查找生成的文件...")
                    for wav_file in upload_dir.glob('*.wav'):
                        logger.info(f"[分离任务] 发现文件: {wav_file}")
                        if 'vocals' in wav_file.name.lower() or 'speak' in wav_file.name.lower():
                            vocals_file = wav_file
                        elif 'instrumental' in wav_file.name.lower() or 'instru' in wav_file.name.lower():
                            instrumental_file = wav_file
                
                result = {}
                if vocals_file:
                    result['vocals'] = str(vocals_file)
                    logger.info(f"[分离任务] 人声文件: {vocals_file}")
                if instrumental_file:
                    result['instrumental'] = str(instrumental_file)
                    logger.info(f"[分离任务] 背景音乐: {instrumental_file}")
                if video_only and video_only.exists():
                    result['videoOnly'] = str(video_only)
                    logger.info(f"[分离任务] 无声视频: {video_only}")
                
                TOOL_TASKS[job_id]['status'] = 'completed'
                TOOL_TASKS[job_id]['progress'] = 100
                TOOL_TASKS[job_id]['result'] = result
                logger.info(f"[分离任务] 任务完成: {job_id}")
                
            except Exception as e:
                logger.error(f"[分离任务] 异常: {e}", exc_info=True)
                if job_id in TOOL_TASKS:
                    TOOL_TASKS[job_id]['status'] = 'error'
                    TOOL_TASKS[job_id]['message'] = str(e)
        
        # 创建任务记录
        TOOL_TASKS[job_id] = {
            'user_id': user_id,
            'status': 'processing',
            'progress': 0,
            'message': f'分离中: {file.filename}',
            'result': None
        }
        
        # 启动异步任务
        asyncio.create_task(separate_task())
        
        return JSONResponse({
            'success': True,
            'data': {
                'taskId': job_id,
                'status': 'processing',
                'message': '开始分离音频'
            }
        })
        
    except Exception as e:
        logger.error(f"Separate audio upload failed: {e}")
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@app.post('/api/tools/separate-video-audio')
async def separate_video_audio_tool(file: UploadFile = File(...)):
    """
    音视频分离工具API - 将视频分离成无声视频和完整音频
    """
    try:
        user_id = 'web_user'
        job_id = str(uuid.uuid4())[:8]

        # 保存上传的文件
        upload_dir = Path('output') / f'separate_va_{job_id}'
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / file.filename
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # 异步执行分离
        async def separate_video_audio_task():
            try:
                logger.info(f"[音视频分离] 开始分离: {file.filename}")
                logger.info(f"[音视频分离] 文件路径: {file_path}")

                # 设置输出文件路径
                base_name = file_path.stem
                video_only_path = upload_dir / f"{base_name}_video_only.mp4"
                full_audio_path = upload_dir / f"{base_name}_full_audio.wav"

                # 设置环境变量，确保UTF-8编码
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'

                # 分离视频流（无声视频）
                TOOL_TASKS[job_id]['progress'] = 30
                TOOL_TASKS[job_id]['message'] = '正在提取视频流...'
                logger.info(f"[音视频分离] 正在提取视频流...")

                cmd_video = [
                    'ffmpeg', '-i', str(file_path),
                    '-an', '-c:v', 'copy',
                    '-y', str(video_only_path)
                ]
                result_video = subprocess.run(
                    cmd_video,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env
                )

                if result_video.returncode != 0:
                    error_msg = f"视频流提取失败: {result_video.stderr}"
                    logger.error(f"[音视频分离] {error_msg}")
                    TOOL_TASKS[job_id]['status'] = 'error'
                    TOOL_TASKS[job_id]['message'] = error_msg
                    return

                logger.info(f"[音视频分离] 视频流提取完成: {video_only_path}")

                # 分离音频流
                TOOL_TASKS[job_id]['progress'] = 60
                TOOL_TASKS[job_id]['message'] = '正在提取音频流...'
                logger.info(f"[音视频分离] 正在提取音频流...")

                cmd_audio = [
                    'ffmpeg', '-i', str(file_path),
                    '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
                    '-y', str(full_audio_path)
                ]
                result_audio = subprocess.run(
                    cmd_audio,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env
                )

                if result_audio.returncode != 0:
                    error_msg = f"音频流提取失败: {result_audio.stderr}"
                    logger.error(f"[音视频分离] {error_msg}")
                    TOOL_TASKS[job_id]['status'] = 'error'
                    TOOL_TASKS[job_id]['message'] = error_msg
                    return

                logger.info(f"[音视频分离] 音频流提取完成: {full_audio_path}")

                # 检查文件是否存在
                if not video_only_path.exists() or not full_audio_path.exists():
                    error_msg = "分离后的文件未生成"
                    logger.error(f"[音视频分离] {error_msg}")
                    TOOL_TASKS[job_id]['status'] = 'error'
                    TOOL_TASKS[job_id]['message'] = error_msg
                    return

                # 完成
                logger.info(f"[音视频分离] 分离完成")
                TOOL_TASKS[job_id]['status'] = 'completed'
                TOOL_TASKS[job_id]['progress'] = 100
                TOOL_TASKS[job_id]['message'] = '音视频分离完成'
                TOOL_TASKS[job_id]['result'] = {
                    'videoOnly': str(video_only_path),
                    'audio': str(full_audio_path),
                    'videoFileName': video_only_path.name,
                    'audioFileName': full_audio_path.name,
                    'videoSize': video_only_path.stat().st_size,
                    'audioSize': full_audio_path.stat().st_size
                }

            except Exception as e:
                logger.error(f"[音视频分离] 异常: {e}")
                import traceback
                traceback.print_exc()
                TOOL_TASKS[job_id]['status'] = 'error'
                TOOL_TASKS[job_id]['message'] = str(e)

        # 注册任务
        TOOL_TASKS[job_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '开始音视频分离',
            'result': None
        }

        # 启动异步任务
        asyncio.create_task(separate_video_audio_task())

        return JSONResponse({
            'success': True,
            'data': {
                'taskId': job_id,
                'status': 'processing',
                'message': '开始音视频分离'
            }
        })

    except Exception as e:
        logger.error(f"Separate video-audio upload failed: {e}")
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@app.post('/api/tools/translate')
async def translate_tool(
    file: UploadFile = File(...),
    targetLang: str = Form('en'),
    contextPrompt: str = Form(''),
    apiType: str = Form('gemini'),
    model: str = Form('')
):
    """
    字幕翻译工具API

    Args:
        file: SRT字幕文件
        targetLang: 目标语言 (zh/en/ja/ko)
        contextPrompt: 用户提供的翻译上下文（语言、内容、专有名词等）
        apiType: 翻译API类型 (gemini/openai)
        model: 翻译模型（可选）
    """
    try:
        user_id = 'web_user'
        job_id = str(uuid.uuid4())[:8]

        # 验证文件格式
        if not file.filename.endswith('.srt'):
            return JSONResponse({
                'success': False,
                'error': '仅支持 SRT 格式字幕文件'
            }, status_code=400)

        # 保存上传的文件
        upload_dir = Path('output') / f'translate_{job_id}'
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / file.filename
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # 异步执行翻译
        async def translate_task():
            try:
                logger.info(f"[翻译任务] 开始翻译: {file.filename}")
                logger.info(f"[翻译任务] 目标语言: {targetLang}")
                logger.info(f"[翻译任务] API类型: {apiType}")
                if contextPrompt:
                    logger.info(f"[翻译任务] 上下文提示: {contextPrompt[:100]}...")

                # 设置输出路径
                output_path = upload_dir / f'{file_path.stem}.translated.srt'

                # 构建翻译命令
                cmd = [
                    sys.executable,
                    'Scripts/step4_translate_srt.py',
                    str(file_path),
                    '--target_lang', targetLang,
                    '-o', str(output_path),
                    '--api_type', apiType
                ]

                # 添加可选参数
                if model:
                    cmd.extend(['--model', model])
                if contextPrompt:
                    cmd.extend(['--context', contextPrompt])

                logger.info(f"[翻译任务] 执行命令: {' '.join(cmd)}")

                # 设置环境变量，确保UTF-8编码
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'

                # 执行翻译
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env
                )

                if result.stdout:
                    logger.info(f"[翻译任务] 标准输出: {result.stdout}")
                if result.stderr:
                    logger.warning(f"[翻译任务] 错误输出: {result.stderr}")

                if result.returncode == 0 and output_path.exists():
                    logger.info(f"[翻译任务] 翻译完成: {output_path}")
                    TOOL_TASKS[job_id]['status'] = 'completed'
                    TOOL_TASKS[job_id]['progress'] = 100
                    TOOL_TASKS[job_id]['message'] = '翻译完成'
                    TOOL_TASKS[job_id]['result'] = {
                        'srt': str(output_path),
                        'fileName': output_path.name,
                        'fileSize': output_path.stat().st_size
                    }
                else:
                    error_msg = result.stderr or '翻译失败'
                    logger.error(f"[翻译任务] 失败: {error_msg}")
                    TOOL_TASKS[job_id]['status'] = 'error'
                    TOOL_TASKS[job_id]['message'] = error_msg

            except Exception as e:
                logger.error(f"[翻译任务] 异常: {e}")
                import traceback
                traceback.print_exc()
                TOOL_TASKS[job_id]['status'] = 'error'
                TOOL_TASKS[job_id]['message'] = str(e)

        # 注册任务
        TOOL_TASKS[job_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '开始翻译字幕',
            'result': None
        }

        # 启动异步任务
        asyncio.create_task(translate_task())

        return JSONResponse({
            'success': True,
            'data': {
                'taskId': job_id,
                'status': 'processing',
                'message': '开始翻译字幕'
            }
        })

    except Exception as e:
        logger.error(f"Translate upload failed: {e}")
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@app.get('/api/tools/download-result/{taskId}/status')
async def get_tool_task_status(taskId: str):
    """
    获取工具任务状态
    """
    if taskId in TOOL_TASKS:
        job = TOOL_TASKS[taskId]
        return JSONResponse({
            'success': True,
            'data': {
                'status': job['status'],
                'progress': job.get('progress', 0),
                'message': job.get('message', ''),
                'result': job.get('result')
            }
        })
    else:
        return JSONResponse({'success': False, 'error': 'Task not found'}, status_code=404)


@app.get('/api/tools/download-result/{taskId}/{fileType}')
async def download_tool_result(taskId: str, fileType: str):
    """
    下载工具生成的文件
    """
    if taskId not in TOOL_TASKS:
        return JSONResponse({'error': 'Task not found'}, status_code=404)
    
    job = TOOL_TASKS[taskId]
    result = job.get('result')
    
    if not result:
        return JSONResponse({'error': 'Result not available'}, status_code=404)
    
    # 根据文件类型返回对应文件
    file_path = None

    if fileType == 'file' and isinstance(result, dict):
        # 视频下载的主文件
        file_path = result.get('filePath')
    elif fileType == 'srt':
        # SRT文件 - 支持两种格式
        if isinstance(result, str):
            # 转录结果（字符串格式）
            file_path = result
        elif isinstance(result, dict):
            # 翻译结果（字典格式）
            file_path = result.get('srt')
    elif fileType in ['vocals', 'instrumental', 'videoOnly', 'audio'] and isinstance(result, dict):
        # 音频/视频分离结果
        file_path = result.get(fileType)
    
    logger.info(f"[文件下载] taskId={taskId}, fileType={fileType}, file_path={file_path}")
    
    if file_path and Path(file_path).exists():
        # 根据文件类型设置 media_type
        media_type = 'application/octet-stream'
        if file_path.endswith(('.mp4', '.mkv', '.avi')):
            media_type = 'video/mp4'
        elif file_path.endswith(('.mp3', '.wav', '.m4a')):
            media_type = 'audio/mpeg'
        elif file_path.endswith('.srt'):
            media_type = 'text/plain'
        
        return FileResponse(
            path=file_path,
            filename=Path(file_path).name,
            media_type=media_type
        )
    else:
        logger.error(f"[文件下载] 文件不存在: {file_path}")
        return JSONResponse({'error': 'File not found', 'path': str(file_path)}, status_code=404)


# ==================== SRT+视频+TTS 工作台 API ====================

@app.get('/api/workbench/health')
async def workbench_health():
    """检查工作台是否可用"""
    if workbench is None:
        return JSONResponse({
            'success': False,
            'error': 'Workbench not available'
        }, status_code=503)

    return JSONResponse({
        'success': True,
        'data': {
            'status': 'available',
            'projects_count': len(workbench.projects)
        }
    })


@app.get('/api/workbench/projects')
async def get_workbench_projects():
    """获取所有项目列表"""
    if workbench is None:
        return JSONResponse({
            'success': False,
            'error': 'Workbench not available'
        }, status_code=503)

    try:
        projects = workbench.list_projects()
        return JSONResponse({
            'success': True,
            'data': projects
        })
    except Exception as e:
        logger.error(f"[工作台] 获取项目列表失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/workbench/projects')
async def create_workbench_project(request: dict):
    """创建新项目"""
    if workbench is None:
        return JSONResponse({
            'success': False,
            'error': 'Workbench not available'
        }, status_code=503)

    try:
        name = request.get('name', '').strip()
        if not name:
            return JSONResponse({
                'success': False,
                'error': 'Project name is required'
            }, status_code=400)

        project_id = workbench.create_project(name)
        return JSONResponse({
            'success': True,
            'data': {
                'project_id': project_id,
                'name': name
            }
        })
    except Exception as e:
        logger.error(f"[工作台] 创建项目失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.get('/api/workbench/projects/{project_id}')
async def get_workbench_project(project_id: str):
    """获取项目详情"""
    if workbench is None:
        return JSONResponse({
            'success': False,
            'error': 'Workbench not available'
        }, status_code=503)

    try:
        if project_id not in workbench.projects:
            return JSONResponse({
                'success': False,
                'error': 'Project not found'
            }, status_code=404)

        project = workbench.projects[project_id]
        project_data = {
            'project_id': project.project_id,
            'name': project.name,
            'video_path': project.video_path,
            'srt_path': project.srt_path,
            'output_dir': project.output_dir,
            'subtitles': [asdict(s) for s in project.subtitles] if project.subtitles else [],
            'video_segments': [asdict(v) for v in project.video_segments] if project.video_segments else [],
            'tts_segments': [asdict(t) for t in project.tts_segments] if project.tts_segments else [],
            'created_at': project.created_at,
            'updated_at': project.updated_at
        }

        return JSONResponse({
            'success': True,
            'data': project_data
        })
    except Exception as e:
        logger.error(f"[工作台] 获取项目详情失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.delete('/api/workbench/projects/{project_id}')
async def delete_workbench_project(project_id: str):
    """删除项目"""
    if workbench is None:
        return JSONResponse({
            'success': False,
            'error': 'Workbench not available'
        }, status_code=503)

    try:
        if project_id not in workbench.projects:
            return JSONResponse({
                'success': False,
                'error': 'Project not found'
            }, status_code=404)

        # TODO: 实现项目删除逻辑（清理文件等）
        del workbench.projects[project_id]

        return JSONResponse({
            'success': True,
            'data': {'message': 'Project deleted successfully'}
        })
    except Exception as e:
        logger.error(f"[工作台] 删除项目失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/workbench/projects/{project_id}/upload-srt')
async def upload_workbench_srt(project_id: str, file: UploadFile = File(...)):
    """上传SRT文件"""
    if workbench is None:
        return JSONResponse({
            'success': False,
            'error': 'Workbench not available'
        }, status_code=503)

    try:
        if project_id not in workbench.projects:
            return JSONResponse({
                'success': False,
                'error': 'Project not found'
            }, status_code=404)

        if not file.filename.endswith('.srt'):
            return JSONResponse({
                'success': False,
                'error': 'Only .srt files are supported'
            }, status_code=400)

        # 保存上传的文件
        upload_dir = Path(workbench.output_dir) / project_id / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        srt_path = upload_dir / file.filename
        with open(srt_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # 加载SRT文件
        success = workbench.load_srt_file(project_id, str(srt_path))
        if not success:
            return JSONResponse({
                'success': False,
                'error': 'Failed to parse SRT file'
            }, status_code=400)

        project = workbench.projects[project_id]
        subtitles_count = len(project.subtitles) if project.subtitles else 0

        return JSONResponse({
            'success': True,
            'data': {
                'message': 'SRT file uploaded and parsed successfully',
                'subtitles_count': subtitles_count,
                'file_path': str(srt_path)
            }
        })
    except Exception as e:
        logger.error(f"[工作台] 上传SRT文件失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/workbench/projects/{project_id}/upload-video')
async def upload_workbench_video(project_id: str, file: UploadFile = File(...)):
    """上传视频文件"""
    if workbench is None:
        return JSONResponse({
            'success': False,
            'error': 'Workbench not available'
        }, status_code=503)

    try:
        if project_id not in workbench.projects:
            return JSONResponse({
                'success': False,
                'error': 'Project not found'
            }, status_code=404)

        # 检查文件类型
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in video_extensions:
            return JSONResponse({
                'success': False,
                'error': f'Only {", ".join(video_extensions)} files are supported'
            }, status_code=400)

        # 保存上传的文件
        upload_dir = Path(workbench.output_dir) / project_id / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        video_path = upload_dir / file.filename
        with open(video_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # 加载视频文件
        success = workbench.load_video_file(project_id, str(video_path))
        if not success:
            return JSONResponse({
                'success': False,
                'error': 'Failed to load video file'
            }, status_code=400)

        return JSONResponse({
            'success': True,
            'data': {
                'message': 'Video file uploaded successfully',
                'file_path': str(video_path)
            }
        })
    except Exception as e:
        logger.error(f"[工作台] 上传视频文件失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/workbench/projects/{project_id}/extract-segments')
async def extract_workbench_segments(project_id: str):
    """提取视频片段"""
    if workbench is None:
        return JSONResponse({
            'success': False,
            'error': 'Workbench not available'
        }, status_code=503)

    try:
        if project_id not in workbench.projects:
            return JSONResponse({
                'success': False,
                'error': 'Project not found'
            }, status_code=404)

        # 启动异步任务提取视频片段
        async def extract_task():
            try:
                success = workbench.extract_video_segments(project_id)
                if success:
                    project = workbench.projects[project_id]
                    segments_count = len(project.video_segments) if project.video_segments else 0
                    TOOL_TASKS[task_id]['result'] = {
                        'success': True,
                        'segments_count': segments_count,
                        'message': 'Video segments extracted successfully'
                    }
                    TOOL_TASKS[task_id]['status'] = 'completed'
                else:
                    TOOL_TASKS[task_id]['result'] = {
                        'success': False,
                        'error': 'Failed to extract video segments'
                    }
                    TOOL_TASKS[task_id]['status'] = 'failed'
            except Exception as e:
                logger.error(f"[工作台] 提取视频片段失败: {e}")
                TOOL_TASKS[task_id]['result'] = {
                    'success': False,
                    'error': str(e)
                }
                TOOL_TASKS[task_id]['status'] = 'failed'

        # 创建任务
        import uuid
        task_id = str(uuid.uuid4())[:8]

        # 注册任务
        TOOL_TASKS[task_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '正在提取视频片段...',
            'result': None
        }

        # 启动异步任务
        asyncio.create_task(extract_task())

        return JSONResponse({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'processing',
                'message': '开始提取视频片段'
            }
        })
    except Exception as e:
        logger.error(f"[工作台] 启动视频片段提取失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/workbench/projects/{project_id}/generate-tts')
async def generate_workbench_tts(project_id: str, request: dict):
    """批量生成TTS"""
    if workbench is None:
        return JSONResponse({
            'success': False,
            'error': 'Workbench not available'
        }, status_code=503)

    try:
        if project_id not in workbench.projects:
            return JSONResponse({
                'success': False,
                'error': 'Project not found'
            }, status_code=404)

        engine = request.get('engine', 'indextts')
        voice_model = request.get('voice_model', '')
        batch_size = request.get('batch_size', 5)

        # 启动异步任务生成TTS
        async def tts_task():
            try:
                success = workbench.generate_tts_batch(project_id, engine, voice_model, batch_size)
                if success:
                    project = workbench.projects[project_id]
                    tts_segments = project.tts_segments if project.tts_segments else []
                    completed_count = len([t for t in tts_segments if t.status == 'completed'])
                    failed_count = len([t for t in tts_segments if t.status == 'failed'])

                    TOOL_TASKS[task_id]['result'] = {
                        'success': True,
                        'total_segments': len(tts_segments),
                        'completed_count': completed_count,
                        'failed_count': failed_count,
                        'message': 'TTS generation completed'
                    }
                    TOOL_TASKS[task_id]['status'] = 'completed'
                else:
                    TOOL_TASKS[task_id]['result'] = {
                        'success': False,
                        'error': 'Failed to generate TTS'
                    }
                    TOOL_TASKS[task_id]['status'] = 'failed'
            except Exception as e:
                logger.error(f"[工作台] TTS生成失败: {e}")
                TOOL_TASKS[task_id]['result'] = {
                    'success': False,
                    'error': str(e)
                }
                TOOL_TASKS[task_id]['status'] = 'failed'

        # 创建任务
        import uuid
        task_id = str(uuid.uuid4())[:8]

        # 注册任务
        TOOL_TASKS[task_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '正在生成TTS...',
            'result': None
        }

        # 启动异步任务
        asyncio.create_task(tts_task())

        return JSONResponse({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'processing',
                'message': '开始生成TTS'
            }
        })
    except Exception as e:
        logger.error(f"[工作台] 启动TTS生成失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/workbench/projects/{project_id}/regenerate-tts/{segment_index}')
async def regenerate_workbench_tts(project_id: str, segment_index: int, request: dict):
    """重新生成单个TTS片段"""
    if workbench is None:
        return JSONResponse({
            'success': False,
            'error': 'Workbench not available'
        }, status_code=503)

    try:
        if project_id not in workbench.projects:
            return JSONResponse({
                'success': False,
                'error': 'Project not found'
            }, status_code=404)

        engine = request.get('engine', 'indextts')
        voice_model = request.get('voice_model', '')

        # 启动异步任务重新生成TTS
        async def regenerate_task():
            try:
                success = workbench.regenerate_single_tts(project_id, segment_index, engine, voice_model)
                if success:
                    project = workbench.projects[project_id]
                    tts_segment = None
                    if project.tts_segments:
                        tts_segment = next((t for t in project.tts_segments if t.index == segment_index), None)

                    TOOL_TASKS[task_id]['result'] = {
                        'success': True,
                        'segment_index': segment_index,
                        'status': tts_segment.status if tts_segment else 'unknown',
                        'message': 'TTS segment regenerated successfully'
                    }
                    TOOL_TASKS[task_id]['status'] = 'completed'
                else:
                    TOOL_TASKS[task_id]['result'] = {
                        'success': False,
                        'error': 'Failed to regenerate TTS segment'
                    }
                    TOOL_TASKS[task_id]['status'] = 'failed'
            except Exception as e:
                logger.error(f"[工作台] TTS重新生成失败: {e}")
                TOOL_TASKS[task_id]['result'] = {
                    'success': False,
                    'error': str(e)
                }
                TOOL_TASKS[task_id]['status'] = 'failed'

        # 创建任务
        import uuid
        task_id = str(uuid.uuid4())[:8]

        # 注册任务
        TOOL_TASKS[task_id] = {
            'status': 'processing',
            'progress': 0,
            'message': f'正在重新生成TTS片段 {segment_index}...',
            'result': None
        }

        # 启动异步任务
        asyncio.create_task(regenerate_task())

        return JSONResponse({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'processing',
                'message': f'开始重新生成TTS片段 {segment_index}'
            }
        })
    except Exception as e:
        logger.error(f"[工作台] 启动TTS重新生成失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.get('/api/workbench/projects/{project_id}/export')
async def export_workbench_project(project_id: str):
    """导出项目摘要"""
    if workbench is None:
        return JSONResponse({
            'success': False,
            'error': 'Workbench not available'
        }, status_code=503)

    try:
        if project_id not in workbench.projects:
            return JSONResponse({
                'success': False,
                'error': 'Project not found'
            }, status_code=404)

        # 导出项目摘要
        export_path = workbench.export_project_summary(project_id)

        if export_path and Path(export_path).exists():
            return FileResponse(
                path=export_path,
                filename=f"project_{project_id}_summary.json",
                media_type='application/json'
            )
        else:
            return JSONResponse({
                'success': False,
                'error': 'Failed to export project summary'
            }, status_code=500)
    except Exception as e:
        logger.error(f"[工作台] 导出项目失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)




# ==================== 字幕切片工具 API ====================

@app.post('/api/tools/upload-srt')
async def upload_srt_file(file: UploadFile = File(...)):
    """上传SRT文件"""
    if not file.filename.endswith('.srt'):
        return JSONResponse({
            'success': False,
            'error': 'Only .srt files are supported'
        }, status_code=400)

    try:
        # 创建临时目录
        temp_dir = Path("temp") / f"srt_{uuid.uuid4().hex[:8]}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        srt_path = temp_dir / file.filename
        with open(srt_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # 解析SRT文件
        import srt
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read().lstrip('\ufeff')

        subtitles = list(srt.parse(srt_content))
        subtitle_segments = []

        for i, subtitle in enumerate(subtitles, 1):
            content = subtitle.content
            speaker = None
            if content.startswith('[') and '] ' in content:
                speaker_end = content.find('] ')
                speaker = content[1:speaker_end]
                content = content[speaker_end + 2:]

            segment = {
                'index': i,
                'start_time': srt.timedelta_to_srt_timestamp(subtitle.start),
                'end_time': srt.timedelta_to_srt_timestamp(subtitle.end),
                'start_seconds': subtitle.start.total_seconds(),
                'end_seconds': subtitle.end.total_seconds(),
                'content': content,
                'speaker': speaker
            }
            subtitle_segments.append(segment)

        return JSONResponse({
            'success': True,
            'data': {
                'subtitles': subtitle_segments,
                'file_path': str(srt_path)
            }
        })

    except Exception as e:
        logger.error(f"[工具] SRT文件上传失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/tools/upload-media')
async def upload_media_file(file: UploadFile = File(...)):
    """上传媒体文件（视频或音频）"""
    # 检查文件类型
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    audio_extensions = ['.mp3', '.wav', '.m4a']
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in video_extensions + audio_extensions:
        return JSONResponse({
            'success': False,
            'error': f'Only {", ".join(video_extensions + audio_extensions)} files are supported'
        }, status_code=400)

    try:
        # 创建临时目录
        temp_dir = Path("temp") / f"media_{uuid.uuid4().hex[:8]}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        media_path = temp_dir / file.filename
        with open(media_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        return JSONResponse({
            'success': True,
            'data': {
                'file_path': str(media_path),
                'file_type': 'video' if file_ext in video_extensions else 'audio'
            }
        })

    except Exception as e:
        logger.error(f"[工具] 媒体文件上传失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/tools/extract-segments')
async def extract_video_segments(
    srt_file: UploadFile = File(None),
    media_file: UploadFile = File(None),
    srt_file_path: str = Form(None),
    media_file_path: str = Form(None),
    subtitles: str = Form(...)
):
    """根据SRT字幕提取视频片段"""
    try:
        import json

        # 解析字幕数据
        subtitle_data = json.loads(subtitles)

        # 处理文件上传或文件路径
        actual_srt_path = None
        actual_media_path = None

        # 处理SRT文件
        if srt_file and srt_file.filename:
            # 如果直接上传了SRT文件
            temp_dir = Path("temp") / f"srt_{uuid.uuid4().hex[:8]}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            actual_srt_path = temp_dir / srt_file.filename
            content = await srt_file.read()
            with open(actual_srt_path, 'wb') as f:
                f.write(content)
        elif srt_file_path and Path(srt_file_path).exists():
            # 如果提供了SRT文件路径
            actual_srt_path = Path(srt_file_path)

        # 处理媒体文件
        if media_file and media_file.filename:
            # 如果直接上传了媒体文件
            temp_dir = Path("temp") / f"media_{uuid.uuid4().hex[:8]}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            actual_media_path = temp_dir / media_file.filename
            content = await media_file.read()
            with open(actual_media_path, 'wb') as f:
                f.write(content)
        elif media_file_path and Path(media_file_path).exists():
            # 如果提供了媒体文件路径
            actual_media_path = Path(media_file_path)

        # 验证必要的文件
        if not actual_media_path:
            return JSONResponse({
                'success': False,
                'error': '媒体文件是必需的'
            }, status_code=400)

        # 创建输出目录
        output_dir = Path("temp") / f"segments_{uuid.uuid4().hex[:8]}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 创建音频切片目录
        audio_output_dir = Path("temp") / f"audio_segments_{uuid.uuid4().hex[:8]}"
        audio_output_dir.mkdir(parents=True, exist_ok=True)

        # 创建任务
        task_id = str(uuid.uuid4())[:8]

        async def extract_task():
            try:
                logger.info(f"[切片工具] 开始提取视频片段: {actual_media_path}")
                logger.info(f"[切片工具] 字幕数量: {len(subtitle_data)}")

                extracted_segments = []

                for i, subtitle in enumerate(subtitle_data):
                    start_time = subtitle['start_seconds']
                    end_time = subtitle['end_seconds']
                    duration = end_time - start_time

                    if duration <= 0:
                        continue

                    # 输出文件路径 - 只生成音频切片
                    audio_file = audio_output_dir / f"segment_{subtitle['index']:03d}.wav"

                    logger.info(f"[切片工具] 提取音频片段 {subtitle['index']}: {start_time:.2f}s - {end_time:.2f}s")

                    # 提取音频切片（用于TTS语音参考）
                    audio_cmd = [
                        'ffmpeg', '-i', str(actual_media_path),
                        '-ss', str(start_time),
                        '-t', str(duration),
                        '-vn', '-acodec', 'pcm_s16le',
                        '-ar', '16000',
                        '-ac', '1',
                        '-y', str(audio_file)
                    ]

                    # 执行音频切片提取
                    audio_result = subprocess.run(
                        audio_cmd,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace'
                    )

                    if audio_result.returncode == 0 and audio_file.exists():
                        segment_info = {
                            'index': subtitle['index'],
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration': duration,
                            'file_path': str(audio_file),  # 音频切片路径
                            'file_size': audio_file.stat().st_size,
                            'subtitle': subtitle['content']
                        }
                        extracted_segments.append(segment_info)

                        # 更新进度
                        progress = int((i + 1) / len(subtitle_data) * 100)
                        TOOL_TASKS[task_id]['progress'] = progress
                        TOOL_TASKS[task_id]['message'] = f'已提取 {i + 1}/{len(subtitle_data)} 个片段'
                    else:
                        logger.warning(f"[切片工具] 片段 {subtitle['index']} 提取失败: {result.stderr}")

                # 完成
                TOOL_TASKS[task_id]['status'] = 'completed'
                TOOL_TASKS[task_id]['progress'] = 100
                TOOL_TASKS[task_id]['message'] = f'成功提取 {len(extracted_segments)} 个视频片段'
                TOOL_TASKS[task_id]['result'] = {
                    'segments': extracted_segments,
                    'output_dir': str(output_dir),
                    'total_segments': len(extracted_segments)
                }

                logger.info(f"[切片工具] 切片完成: {len(extracted_segments)} 个片段")

                # 清理临时文件（延迟清理，避免文件锁定）
                try:
                    import threading
                    import time

                    def cleanup_temp_files():
                        time.sleep(5)  # 等待5秒确保文件不再被使用
                        try:
                            # 清理上传的临时文件
                            if srt_file and srt_file.filename and actual_srt_path and actual_srt_path.parent.name.startswith('srt_'):
                                import shutil
                                shutil.rmtree(actual_srt_path.parent, ignore_errors=True)
                                logger.info(f"[切片工具] 已清理SRT临时文件: {actual_srt_path.parent}")

                            if media_file and media_file.filename and actual_media_path and actual_media_path.parent.name.startswith('media_'):
                                import shutil
                                shutil.rmtree(actual_media_path.parent, ignore_errors=True)
                                logger.info(f"[切片工具] 已清理媒体临时文件: {actual_media_path.parent}")
                        except Exception as cleanup_error:
                            logger.warning(f"[切片工具] 清理临时文件时出错: {cleanup_error}")

                    # 启动清理线程
                    cleanup_thread = threading.Thread(target=cleanup_temp_files, daemon=True)
                    cleanup_thread.start()

                except Exception as e:
                    logger.warning(f"[切片工具] 启动清理任务失败: {e}")

            except Exception as e:
                logger.error(f"[切片工具] 切片失败: {e}")
                TOOL_TASKS[task_id]['status'] = 'failed'
                TOOL_TASKS[task_id]['message'] = f'切片失败: {str(e)}'
                TOOL_TASKS[task_id]['result'] = {'error': str(e)}

        # 注册任务
        TOOL_TASKS[task_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '开始提取视频片段...',
            'result': None
        }

        # 启动异步任务
        asyncio.create_task(extract_task())

        return JSONResponse({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'processing',
                'message': '开始提取视频片段'
            }
        })

    except Exception as e:
        logger.error(f"[切片工具] 启动切片失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/tools/upload-voice')
async def upload_voice_file(file: UploadFile = File(...)):
    """上传TTS语音参考文件"""
    if not file.filename.endswith('.wav'):
        return JSONResponse({
            'success': False,
            'error': 'Only .wav files are supported for voice reference'
        }, status_code=400)

    try:
        # 创建voice文件目录
        voice_dir = Path("temp") / f"voice_{uuid.uuid4().hex[:8]}"
        voice_dir.mkdir(parents=True, exist_ok=True)

        voice_path = voice_dir / file.filename
        with open(voice_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        return JSONResponse({
            'success': True,
            'data': {
                'voice_path': str(voice_path),
                'file_name': file.filename,
                'file_size': voice_path.stat().st_size
            }
        })

    except Exception as e:
        logger.error(f"[工具] 语音文件上传失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/tools/generate-tts')
async def generate_tts_segments(
    subtitles: str = Form(...),
    engine: str = Form('indextts'),
    segments_json: str = Form(None),  # 接收已提取的音频切片信息
    prompt_lang: str = Form('zh'),  # GPT-SoVITS: 输入语言（参考音频语言）
    text_lang: str = Form('zh')      # GPT-SoVITS: 输出语言（目标语言）
):
    """为字幕片段生成TTS，使用对应的音频切片作为语音参考

    支持的TTS引擎：
    - indextts: IndexTTS (中文/英文)
    - gptsovits: GPT-SoVITS (中文/英文/日文/韩文)
    """
    try:
        import json

        # 解析字幕数据
        subtitle_data = json.loads(subtitles)

        # 解析音频切片数据
        audio_segments = []
        if segments_json:
            try:
                audio_segments = json.loads(segments_json)
                logger.info(f"[TTS工具] 收到 {len(audio_segments)} 个音频切片")
            except Exception as e:
                logger.warning(f"[TTS工具] 解析音频切片数据失败: {e}")

        # 创建输出目录
        output_dir = Path("temp") / f"tts_{uuid.uuid4().hex[:8]}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 创建任务
        task_id = str(uuid.uuid4())[:8]

        async def tts_task():
            try:
                logger.info(f"[TTS工具] 开始生成TTS: 引擎={engine}, 字幕数量={len(subtitle_data)}")
                logger.info(f"[TTS工具] 可用音频切片数量: {len(audio_segments)}")

                tts_segments = []

                # 初始化TTS实例（在循环外，避免重复初始化导致内存泄漏）
                tts = None
                gptsovits = None

                if engine.lower() == 'indextts':
                    try:
                        # 添加IndexTTS到路径
                        project_root = PROJECT_ROOT
                        idx_root = (project_root / 'tools' / 'index-tts').resolve()
                        if str(idx_root) not in sys.path:
                            sys.path.insert(0, str(idx_root))

                        from indextts.infer_v2 import IndexTTS2
                        import torch

                        # 配置IndexTTS2
                        config_path = idx_root / "checkpoints" / "config.yaml"
                        model_dir = idx_root / "checkpoints"

                        if not config_path.exists():
                            raise Exception(f"IndexTTS2配置文件不存在: {config_path}")

                        # 清理GPU内存（如果有的话）
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                            logger.info("[TTS工具] 已清理CUDA缓存")

                        # 初始化IndexTTS2 - 与pipeline保持一致
                        logger.info("[TTS工具] 初始化IndexTTS2...")
                        tts = IndexTTS2(cfg_path=str(config_path), model_dir=str(model_dir), use_cuda_kernel=False)
                        logger.info("[TTS工具] IndexTTS2初始化完成")
                    except Exception as e:
                        error_msg = f"IndexTTS2初始化失败: {str(e)}"
                        logger.error(f"[TTS工具] {error_msg}")
                        raise Exception(error_msg)
                elif engine.lower() == 'gptsovits':
                    try:
                        # 添加 GPT-SoVITS 和 Scripts 路径到系统路径
                        project_root = PROJECT_ROOT
                        gptsovits_root = project_root / 'tools' / 'GPT-SoVITS'
                        gptsovits_lib = gptsovits_root / 'GPT_SoVITS'
                        scripts_root = project_root / 'Scripts'

                        # GPTSoVITSTTS 类内部会自己处理工作目录切换，我们只需要确保 sys.path 正确
                        for path in [str(scripts_root), str(gptsovits_root), str(gptsovits_lib)]:
                            if path not in sys.path:
                                sys.path.insert(0, path)

                        from step6_tts_gptsovits import GPTSoVITSTTS

                        # 初始化 GPT-SoVITS（使用本地模式）
                        # 不需要切换工作目录，GPTSoVITSTTS 内部会处理
                        logger.info("[TTS工具] 初始化GPT-SoVITS...")
                        gptsovits = GPTSoVITSTTS(mode="local")
                        logger.info("[TTS工具] GPT-SoVITS初始化完成")
                    except Exception as e:
                        error_msg = f"GPT-SoVITS初始化失败: {str(e)}"
                        logger.error(f"[TTS工具] {error_msg}")
                        raise Exception(error_msg)

                for i, subtitle in enumerate(subtitle_data):
                    text = subtitle['content']
                    if not text.strip():
                        continue

                    # 查找对应的音频切片 - 语音参考是必须的
                    voice_path = None
                    matching_segment = next((seg for seg in audio_segments if seg['index'] == subtitle['index']), None)

                    if matching_segment and 'file_path' in matching_segment:
                        voice_path = Path(matching_segment['file_path'])
                        if voice_path.exists():
                            logger.info(f"[TTS工具] 片段 {subtitle['index']} 使用音频切片: {voice_path}")
                        else:
                            # 音频切片文件不存在 - 这是严重错误
                            error_msg = f"片段 {subtitle['index']} 的音频切片文件不存在: {voice_path}"
                            logger.error(f"[TTS工具] {error_msg}")
                            segment_info = {
                                'index': subtitle['index'],
                                'text': text,
                                'audio_path': '',
                                'duration': 0.0,
                                'file_size': 0,
                                'engine': engine,
                                'status': 'failed',
                                'error': error_msg
                            }
                            tts_segments.append(segment_info)
                            continue
                    else:
                        # 未找到对应的音频切片 - 这是严重错误
                        error_msg = f"片段 {subtitle['index']} 未找到对应的音频切片，无法生成TTS"
                        logger.error(f"[TTS工具] {error_msg}")
                        segment_info = {
                            'index': subtitle['index'],
                            'text': text,
                            'audio_path': '',
                            'duration': 0.0,
                            'file_size': 0,
                            'engine': engine,
                            'status': 'failed',
                            'error': error_msg
                        }
                        tts_segments.append(segment_info)
                        continue

                    # 输出文件路径
                    output_file = output_dir / f"tts_{subtitle['index']:03d}.wav"

                    # 使用IndexTTS2生成语音 - 必须使用音频切片作为语音参考
                    if engine.lower() == 'indextts':
                        try:
                            if tts is None:
                                raise Exception("IndexTTS2未初始化")

                            # 生成TTS语音 - 使用音频切片作为说话人参考
                            logger.info(f"[TTS工具] 片段 {subtitle['index']} 使用IndexTTS2生成语音: {voice_path}")
                            tts.infer(
                                spk_audio_prompt=str(voice_path),
                                text=text,
                                output_path=str(output_file),
                                verbose=False
                            )

                            # 清理GPU内存（每个片段生成后）
                            import torch
                            if torch.cuda.is_available():
                                torch.cuda.empty_cache()

                            # 验证输出文件是否生成
                            if output_file.exists():
                                duration = get_audio_duration(output_file)
                                file_size = output_file.stat().st_size
                                logger.info(f"[TTS工具] 片段 {subtitle['index']} TTS生成成功: {output_file}")

                                segment_info = {
                                    'index': subtitle['index'],
                                    'text': text,
                                    'audio_path': str(output_file),
                                    'duration': duration,
                                    'file_size': file_size,
                                    'engine': engine,
                                    'status': 'completed',
                                    'voice_source': 'segment' if voice_path and voice_path.exists() else 'default',
                                    'error': ''
                                }
                            else:
                                raise Exception("TTS生成失败：输出文件未创建")

                        except Exception as e:
                            error_msg = f"IndexTTS2生成失败: {str(e)}"
                            logger.error(f"[TTS工具] {error_msg}")
                            segment_info = {
                                'index': subtitle['index'],
                                'text': text,
                                'audio_path': '',
                                'duration': 0.0,
                                'file_size': 0,
                                'engine': engine,
                                'status': 'failed',
                                'voice_source': 'none',
                                'error': error_msg
                            }
                    elif engine.lower() == 'gptsovits':
                        # GPT-SoVITS 生成
                        try:
                            if gptsovits is None:
                                raise Exception("GPT-SoVITS未初始化")

                            # 生成TTS语音 - 使用音频切片作为参考，无参考文本模式
                            logger.info(f"[TTS工具] 片段 {subtitle['index']} 使用GPT-SoVITS生成语音")
                            logger.info(f"  - 参考音频: {voice_path}")
                            logger.info(f"  - 输入语言: {prompt_lang}, 输出语言: {text_lang}")

                            success = gptsovits.synthesize_single(
                                text=text,
                                text_lang=text_lang,
                                ref_audio_path=str(voice_path),
                                prompt_text="",  # 使用无参考文本模式
                                prompt_lang=prompt_lang,
                                output_path=str(output_file)
                            )

                            if success and output_file.exists():
                                duration = get_audio_duration(output_file)
                                file_size = output_file.stat().st_size
                                logger.info(f"[TTS工具] 片段 {subtitle['index']} GPT-SoVITS生成成功: {output_file}")

                                segment_info = {
                                    'index': subtitle['index'],
                                    'text': text,
                                    'audio_path': str(output_file),
                                    'duration': duration,
                                    'file_size': file_size,
                                    'engine': engine,
                                    'status': 'completed',
                                    'voice_source': 'segment' if voice_path and voice_path.exists() else 'default',
                                    'error': ''
                                }
                            else:
                                raise Exception("GPT-SoVITS生成失败：输出文件未创建或生成失败")

                        except Exception as e:
                            error_msg = f"GPT-SoVITS生成失败: {str(e)}"
                            logger.error(f"[TTS工具] {error_msg}")
                            segment_info = {
                                'index': subtitle['index'],
                                'text': text,
                                'audio_path': '',
                                'duration': 0.0,
                                'file_size': 0,
                                'engine': engine,
                                'status': 'failed',
                                'voice_source': 'none',
                                'error': error_msg
                            }
                    else:
                        # 不支持的TTS引擎
                        logger.warning(f"[TTS工具] 不支持的TTS引擎: {engine}")
                        segment_info = {
                            'index': subtitle['index'],
                            'text': text,
                            'audio_path': '',
                            'duration': 0.0,
                            'file_size': 0,
                            'engine': engine,
                            'status': 'failed',
                            'voice_source': 'none',
                            'error': f"不支持的TTS引擎: {engine}"
                        }

                    # 将segment_info添加到结果列表
                    tts_segments.append(segment_info)

                    # 实时更新进度和结果（每个片段生成后立即更新）
                    progress = int((i + 1) / len(subtitle_data) * 100)
                    successful_count = len([s for s in tts_segments if s["status"] == "completed"])
                    TOOL_TASKS[task_id]['progress'] = progress
                    TOOL_TASKS[task_id]['message'] = f'已生成 {i + 1}/{len(subtitle_data)} 个TTS片段 ({successful_count} 个成功)'
                    # 实时更新result，让前端能够立即获取到新生成的片段
                    TOOL_TASKS[task_id]['result'] = {
                        'tts_segments': tts_segments.copy(),  # 使用copy避免引用问题
                        'output_dir': str(output_dir),
                        'total_segments': len(tts_segments),
                        'successful_segments': successful_count,
                        'is_partial': True  # 标记为部分结果
                    }

                # 完成
                TOOL_TASKS[task_id]['status'] = 'completed'
                TOOL_TASKS[task_id]['progress'] = 100
                successful_count = len([s for s in tts_segments if s["status"] == "completed"])
                TOOL_TASKS[task_id]['message'] = f'TTS生成完成: {successful_count} 个成功'
                TOOL_TASKS[task_id]['result'] = {
                    'tts_segments': tts_segments,  # 修复：统一字段名，与前端期待一致
                    'output_dir': str(output_dir),
                    'total_segments': len(tts_segments),
                    'successful_segments': successful_count,
                    'is_partial': False  # 标记为最终结果
                }

                logger.info(f"[TTS工具] TTS生成完成: {successful_count}/{len(tts_segments)} 成功")

            except Exception as e:
                logger.error(f"[TTS工具] TTS生成失败: {e}")
                TOOL_TASKS[task_id]['status'] = 'failed'
                TOOL_TASKS[task_id]['message'] = f'TTS生成失败: {str(e)}'
                TOOL_TASKS[task_id]['result'] = {'error': str(e)}
            finally:
                # 清理资源
                try:
                    if tts is not None:
                        del tts
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    logger.info("[TTS工具] 资源清理完成")
                except Exception as cleanup_error:
                    logger.warning(f"[TTS工具] 资源清理时出错: {cleanup_error}")

        # 注册任务
        TOOL_TASKS[task_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '开始生成TTS...',
            'result': None
        }

        # 启动异步任务
        asyncio.create_task(tts_task())

        return JSONResponse({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'processing',
                'message': '开始生成TTS'
            }
        })

    except Exception as e:
        logger.error(f"[TTS工具] 启动TTS生成失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.get('/api/tools/audio/{audio_path:path}')
async def serve_audio_file(audio_path: str):
    """提供音频文件访问服务"""
    try:
        # 解码路径
        from urllib.parse import unquote
        audio_path = unquote(audio_path)

        # 转换为Path对象
        file_path = Path(audio_path)

        # 安全检查：确保文件在允许的目录下
        allowed_dirs = [Path('temp'), Path('output'), Path('workbench_web')]
        is_allowed = any(
            file_path.resolve().is_relative_to(allowed_dir.resolve())
            for allowed_dir in allowed_dirs
            if allowed_dir.exists()
        )

        if not is_allowed:
            logger.warning(f"[音频服务] 尝试访问不允许的路径: {audio_path}")
            return JSONResponse({
                'success': False,
                'error': '访问被拒绝'
            }, status_code=403)

        # 检查文件是否存在
        if not file_path.exists():
            logger.warning(f"[音频服务] 文件不存在: {audio_path}")
            return JSONResponse({
                'success': False,
                'error': '文件不存在'
            }, status_code=404)

        # 返回音频文件
        logger.info(f"[音频服务] 提供音频文件: {audio_path}")
        return FileResponse(
            path=str(file_path),
            media_type='audio/wav',
            filename=file_path.name
        )

    except Exception as e:
        logger.error(f"[音频服务] 提供音频文件失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/tools/regenerate-tts')
async def regenerate_single_tts(
    segment_index: int = Form(...),
    subtitles: str = Form(...),
    segments_json: str = Form(...),
    engine: str = Form('indextts'),
    prompt_lang: str = Form('zh'),  # GPT-SoVITS: 输入语言（参考音频语言）
    text_lang: str = Form('zh')      # GPT-SoVITS: 输出语言（目标语言）
):
    """重新生成单个TTS片段

    支持的TTS引擎：
    - indextts: IndexTTS (中文/英文)
    - gptsovits: GPT-SoVITS (中文/英文/日文/韩文)
    """
    try:
        import json

        # 解析数据
        subtitle_data = json.loads(subtitles)
        audio_segments = json.loads(segments_json)

        # 找到要重新生成的字幕
        target_subtitle = next((s for s in subtitle_data if s['index'] == segment_index), None)
        if not target_subtitle:
            return JSONResponse({
                'success': False,
                'error': f'未找到片段 {segment_index}'
            }, status_code=404)

        # 找到对应的音频切片
        matching_segment = next((seg for seg in audio_segments if seg['index'] == segment_index), None)
        if not matching_segment or 'file_path' not in matching_segment:
            return JSONResponse({
                'success': False,
                'error': f'片段 {segment_index} 缺少音频切片'
            }, status_code=400)

        voice_path = Path(matching_segment['file_path'])
        if not voice_path.exists():
            return JSONResponse({
                'success': False,
                'error': f'音频切片文件不存在: {voice_path}'
            }, status_code=404)

        # 创建输出目录
        output_dir = Path("temp") / f"tts_regen_{uuid.uuid4().hex[:8]}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"tts_{segment_index:03d}.wav"

        # 创建任务
        task_id = str(uuid.uuid4())[:8]

        async def regenerate_task():
            tts = None
            try:
                text = target_subtitle['content']
                logger.info(f"[TTS工具] 重新生成片段 {segment_index}: {text}")

                # 初始化TTS
                if engine.lower() == 'indextts':
                    project_root = Path(__file__).resolve().parent
                    idx_root = (project_root / 'tools' / 'index-tts').resolve()
                    if str(idx_root) not in sys.path:
                        sys.path.insert(0, str(idx_root))

                    from indextts.infer_v2 import IndexTTS2
                    import torch

                    config_path = idx_root / "checkpoints" / "config.yaml"
                    model_dir = idx_root / "checkpoints"

                    if not config_path.exists():
                        raise Exception(f"IndexTTS2配置文件不存在: {config_path}")

                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

                    # 初始化IndexTTS2 - 与pipeline保持一致
                    logger.info("[TTS工具] Regenerate - 初始化IndexTTS2...")
                    tts = IndexTTS2(cfg_path=str(config_path), model_dir=str(model_dir), use_cuda_kernel=False)
                    logger.info("[TTS工具] Regenerate - IndexTTS2初始化完成")

                    # 生成TTS
                    tts.infer(
                        spk_audio_prompt=str(voice_path),
                        text=text,
                        output_path=str(output_file),
                        verbose=False
                    )

                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

                    if output_file.exists():
                        duration = get_audio_duration(output_file)
                        file_size = output_file.stat().st_size

                        tts_segment = {
                            'index': segment_index,
                            'text': text,
                            'audio_path': str(output_file),
                            'duration': duration,
                            'file_size': file_size,
                            'engine': engine,
                            'status': 'completed',
                            'error': ''
                        }

                        TOOL_TASKS[task_id]['status'] = 'completed'
                        TOOL_TASKS[task_id]['progress'] = 100
                        TOOL_TASKS[task_id]['message'] = f'片段 {segment_index} 重新生成完成'
                        TOOL_TASKS[task_id]['result'] = {
                            'tts_segment': tts_segment
                        }
                        logger.info(f"[TTS工具] 片段 {segment_index} 重新生成成功")
                    else:
                        raise Exception("输出文件未创建")
                elif engine.lower() == 'gptsovits':
                    # GPT-SoVITS 生成
                    project_root = Path(__file__).resolve().parent
                    gptsovits_root = project_root / 'tools' / 'GPT-SoVITS'
                    gptsovits_lib = gptsovits_root / 'GPT_SoVITS'
                    scripts_root = project_root / 'Scripts'

                    # GPTSoVITSTTS 类内部会自己处理工作目录切换，我们只需要确保 sys.path 正确
                    for path in [str(scripts_root), str(gptsovits_root), str(gptsovits_lib)]:
                        if path not in sys.path:
                            sys.path.insert(0, path)

                    from step6_tts_gptsovits import GPTSoVITSTTS

                    # 初始化 GPT-SoVITS（使用本地模式）
                    # 不需要切换工作目录，GPTSoVITSTTS 内部会处理
                    logger.info("[TTS工具] Regenerate - 初始化GPT-SoVITS...")
                    gptsovits = GPTSoVITSTTS(mode="local")
                    logger.info("[TTS工具] Regenerate - GPT-SoVITS初始化完成")

                    # 生成TTS语音
                    logger.info(f"[TTS工具] Regenerate - 片段 {segment_index} 使用GPT-SoVITS生成语音")
                    logger.info(f"  - 参考音频: {voice_path}")
                    logger.info(f"  - 输入语言: {prompt_lang}, 输出语言: {text_lang}")

                    success = gptsovits.synthesize_single(
                        text=text,
                        text_lang=text_lang,
                        ref_audio_path=str(voice_path),
                        prompt_text="",  # 使用无参考文本模式
                        prompt_lang=prompt_lang,
                        output_path=str(output_file)
                    )

                    if success and output_file.exists():
                        duration = get_audio_duration(output_file)
                        file_size = output_file.stat().st_size

                        tts_segment = {
                            'index': segment_index,
                            'text': text,
                            'audio_path': str(output_file),
                            'duration': duration,
                            'file_size': file_size,
                            'engine': engine,
                            'status': 'completed',
                            'error': ''
                        }

                        TOOL_TASKS[task_id]['status'] = 'completed'
                        TOOL_TASKS[task_id]['progress'] = 100
                        TOOL_TASKS[task_id]['message'] = f'片段 {segment_index} 重新生成完成'
                        TOOL_TASKS[task_id]['result'] = {
                            'tts_segment': tts_segment
                        }
                        logger.info(f"[TTS工具] 片段 {segment_index} GPT-SoVITS重新生成成功")
                    else:
                        raise Exception("GPT-SoVITS生成失败：输出文件未创建或生成失败")
                else:
                    raise Exception(f"不支持的TTS引擎: {engine}")

            except Exception as e:
                logger.error(f"[TTS工具] 片段 {segment_index} 重新生成失败: {e}")
                TOOL_TASKS[task_id]['status'] = 'failed'
                TOOL_TASKS[task_id]['message'] = f'重新生成失败: {str(e)}'
                TOOL_TASKS[task_id]['result'] = {'error': str(e)}
            finally:
                try:
                    if tts is not None:
                        del tts
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    pass

        # 注册任务
        TOOL_TASKS[task_id] = {
            'status': 'processing',
            'progress': 0,
            'message': f'开始重新生成片段 {segment_index}...',
            'result': None
        }

        # 启动异步任务
        asyncio.create_task(regenerate_task())

        return JSONResponse({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'processing',
                'message': f'开始重新生成片段 {segment_index}'
            }
        })

    except Exception as e:
        logger.error(f"[TTS工具] 启动重新生成失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/tools/merge-tts-audio')
async def merge_tts_audio(
    subtitles: str = Form(...),
    tts_segments: str = Form(...),
    output_filename: str = Form('merged_tts.wav'),
    source_audio_path: str = Form(None)
):
    """
    合并TTS音频切片为完整音频文件
    使用ffmpeg根据字幕时间戳进行时间轴对齐

    参数:
        subtitles: 字幕数据JSON
        tts_segments: TTS片段数据JSON
        output_filename: 输出文件名
        source_audio_path: 源音频路径（可选），用于响度匹配
    """
    task_id = f"merge-tts-{int(time.time() * 1000)}"

    try:
        import json
        from datetime import timedelta

        # 解析输入
        subtitle_data = json.loads(subtitles)
        tts_segment_data = json.loads(tts_segments)

        logger.info(f"[音频合并] 开始合并 {len(subtitle_data)} 个TTS切片")

        # 创建任务
        async def merge_task():
            try:
                TOOL_TASKS[task_id]['status'] = 'processing'
                TOOL_TASKS[task_id]['progress'] = 10
                TOOL_TASKS[task_id]['message'] = '正在准备音频文件...'

                # 创建输出目录
                output_dir = Path('temp/merged_audio').resolve()  # 转换为绝对路径
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / output_filename

                # 收集有效的TTS切片
                valid_segments = []
                for i, segment in enumerate(tts_segment_data):
                    if segment.get('status') == 'completed' and segment.get('audio_path'):
                        audio_path = Path(segment['audio_path'])
                        if audio_path.exists():
                            # 获取对应的字幕时间戳
                            subtitle = subtitle_data[i] if i < len(subtitle_data) else None
                            if subtitle:
                                valid_segments.append({
                                    'index': i,
                                    'audio_path': audio_path,
                                    'start_time': subtitle.get('start_time', '00:00:00,000'),
                                    'end_time': subtitle.get('end_time', '00:00:00,000')
                                })

                if not valid_segments:
                    raise Exception("没有找到有效的TTS切片")

                logger.info(f"[音频合并] 找到 {len(valid_segments)} 个有效切片")
                TOOL_TASKS[task_id]['progress'] = 20
                TOOL_TASKS[task_id]['message'] = f'找到 {len(valid_segments)} 个有效切片'

                # 解析时间戳为毫秒
                def parse_timestamp(ts: str) -> int:
                    """将SRT时间戳转换为毫秒"""
                    parts = ts.replace(',', ':').split(':')
                    if len(parts) == 4:
                        h, m, s, ms = parts
                        return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
                    return 0

                # 计算总时长（取最后一个字幕的结束时间）
                max_end_time = max([parse_timestamp(seg['end_time']) for seg in valid_segments])
                total_duration_sec = (max_end_time / 1000.0) + 2.0  # 额外加2秒缓冲

                logger.info(f"[音频合并] 总时长约: {total_duration_sec:.2f}秒")
                TOOL_TASKS[task_id]['progress'] = 30

                # 构建ffmpeg filter_complex命令
                # 策略：为每个切片添加延迟(adelay)，然后混音(amix)
                filter_parts = []
                input_files = []

                for idx, seg in enumerate(valid_segments):
                    start_ms = parse_timestamp(seg['start_time'])
                    input_files.extend(['-i', str(seg['audio_path'])])

                    # 为每个输入添加延迟滤镜
                    if start_ms > 0:
                        filter_parts.append(f"[{idx}:a]adelay={start_ms}|{start_ms}[a{idx}]")
                    else:
                        filter_parts.append(f"[{idx}:a]acopy[a{idx}]")

                # 混音所有延迟后的音频流
                mix_inputs = ''.join([f"[a{i}]" for i in range(len(valid_segments))])
                filter_parts.append(f"{mix_inputs}amix=inputs={len(valid_segments)}:duration=longest:dropout_transition=0[aout]")

                filter_complex = ';'.join(filter_parts)

                TOOL_TASKS[task_id]['progress'] = 40
                TOOL_TASKS[task_id]['message'] = '正在执行音频合并...'

                # 构建完整的ffmpeg命令
                cmd = [
                    'ffmpeg', '-y',
                    *input_files,
                    '-filter_complex', filter_complex,
                    '-map', '[aout]',
                    '-ar', '22050',  # 采样率
                    '-ac', '1',      # 单声道
                    '-t', str(total_duration_sec),  # 限制总时长
                    str(output_path)
                ]

                logger.info(f"[音频合并] 执行ffmpeg命令...")
                logger.debug(f"[音频合并] 命令: {' '.join(cmd)}")

                # 执行ffmpeg
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )

                if result.returncode != 0:
                    logger.error(f"[音频合并] ffmpeg错误: {result.stderr}")
                    raise Exception(f"ffmpeg合并失败: {result.stderr[:200]}")

                if not output_path.exists():
                    raise Exception("合并后的音频文件未创建")

                # 响度匹配（如果提供了源音频）
                if source_audio_path:
                    source_path = Path(source_audio_path)
                    if source_path.exists():
                        logger.info(f"[音频合并] 开始响度匹配，参考音频: {source_path}")
                        TOOL_TASKS[task_id]['progress'] = 80
                        TOOL_TASKS[task_id]['message'] = '正在进行响度匹配...'

                        # 分析源音频响度
                        analyze_cmd = [
                            'ffmpeg', '-i', str(source_path),
                            '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json',
                            '-f', 'null', '-'
                        ]

                        analyze_result = subprocess.run(
                            analyze_cmd,
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            errors='ignore'
                        )

                        # 从 stderr 中提取响度信息
                        try:
                            # FFmpeg 的 loudnorm 输出在 stderr 中
                            stderr_lines = analyze_result.stderr.split('\n')
                            json_start = False
                            json_lines = []
                            for line in stderr_lines:
                                if '{' in line:
                                    json_start = True
                                if json_start:
                                    json_lines.append(line)
                                if '}' in line and json_start:
                                    break

                            if json_lines:
                                loudness_info = json.loads(''.join(json_lines))
                                input_i = loudness_info.get('input_i', '-16')
                                input_tp = loudness_info.get('input_tp', '-1.5')
                                input_lra = loudness_info.get('input_lra', '11')
                                input_thresh = loudness_info.get('input_thresh', '-26')

                                logger.info(f"[音频合并] 源音频响度: I={input_i}, TP={input_tp}, LRA={input_lra}")

                                # 应用响度归一化到合并后的音频
                                normalized_path = output_dir / f"normalized_{output_filename}"

                                normalize_cmd = [
                                    'ffmpeg', '-y', '-i', str(output_path),
                                    '-af', f'loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:linear=true:print_format=summary',
                                    '-ar', '22050',
                                    str(normalized_path)
                                ]

                                normalize_result = subprocess.run(
                                    normalize_cmd,
                                    capture_output=True,
                                    text=True,
                                    encoding='utf-8',
                                    errors='ignore'
                                )

                                if normalize_result.returncode == 0 and normalized_path.exists():
                                    # 替换原文件
                                    output_path.unlink()
                                    normalized_path.rename(output_path)
                                    logger.info(f"[音频合并] 响度匹配完成")
                                else:
                                    logger.warning(f"[音频合并] 响度匹配失败，使用原音频: {normalize_result.stderr[:200]}")
                            else:
                                logger.warning(f"[音频合并] 无法解析源音频响度信息")
                        except Exception as e:
                            logger.warning(f"[音频合并] 响度匹配失败: {e}，使用原音频")
                    else:
                        logger.warning(f"[音频合并] 源音频文件不存在: {source_audio_path}")

                TOOL_TASKS[task_id]['progress'] = 90
                TOOL_TASKS[task_id]['message'] = '正在完成处理...'

                # 获取文件大小
                file_size = output_path.stat().st_size
                file_size_mb = file_size / (1024 * 1024)

                TOOL_TASKS[task_id]['status'] = 'completed'
                TOOL_TASKS[task_id]['progress'] = 100
                TOOL_TASKS[task_id]['message'] = '音频合并完成'
                TOOL_TASKS[task_id]['result'] = {
                    'audio_path': str(output_path.relative_to(Path.cwd())),
                    'file_size': file_size,
                    'file_size_mb': round(file_size_mb, 2),
                    'duration_sec': total_duration_sec,
                    'segment_count': len(valid_segments)
                }

                logger.info(f"[音频合并] 完成: {output_path} ({file_size_mb:.2f}MB)")

            except Exception as e:
                logger.error(f"[音频合并] 失败: {e}")
                TOOL_TASKS[task_id]['status'] = 'failed'
                TOOL_TASKS[task_id]['message'] = f'合并失败: {str(e)}'
                TOOL_TASKS[task_id]['result'] = {'error': str(e)}

        # 注册任务
        TOOL_TASKS[task_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '开始音频合并...',
            'result': None
        }

        # 启动异步任务
        asyncio.create_task(merge_task())

        return JSONResponse({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'processing',
                'message': '开始音频合并'
            }
        })

    except Exception as e:
        logger.error(f"[音频合并] 启动失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post('/api/tools/mux-audio-video')
async def mux_audio_video(
    video_file: UploadFile = File(None),
    audio_files: List[UploadFile] = File(None),
    video_path: str = Form(None),
    audio_path: str = Form(None),
    output_filename: str = Form(None)
):
    """
    合成音频和视频轨道为完整视频文件
    使用ffmpeg将音频和视频合成，支持多音频轨道混音

    参数:
        video_file: 上传的视频文件 (可选)
        audio_files: 上传的音频文件列表 (可选，支持多个)
        video_path: 已存在的视频文件路径 (可选)
        audio_path: 已存在的音频文件路径 (可选)
        output_filename: 输出文件名 (可选)
    """
    task_id = f"mux-{int(time.time() * 1000)}"

    try:
        import json

        # 验证输入
        if not video_file and not video_path:
            return JSONResponse({
                'success': False,
                'error': '需要提供视频文件或视频路径'
            }, status_code=400)

        if not audio_files and not audio_path:
            return JSONResponse({
                'success': False,
                'error': '需要提供音频文件或音频路径'
            }, status_code=400)

        logger.info(f"[音视频合成] 开始合成任务 {task_id}, 音频轨道数: {len(audio_files) if audio_files else 1}")

        # 创建临时目录
        temp_dir = Path('temp/mux')
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 立即处理视频文件（在异步任务外）
        video_file_path = None
        if video_file:
            video_file_path = temp_dir / f"video_{task_id}{Path(video_file.filename).suffix}"
            with open(video_file_path, 'wb') as f:
                content = await video_file.read()
                f.write(content)
            logger.info(f"[音视频合成] 视频文件已上传: {video_file_path}")
        elif video_path:
            video_file_path = Path(video_path)
            if not video_file_path.exists():
                return JSONResponse({
                    'success': False,
                    'error': f'视频文件不存在: {video_path}'
                }, status_code=400)
            logger.info(f"[音视频合成] 使用现有视频: {video_file_path}")

        # 立即处理音频文件（在异步任务外）
        audio_file_paths = []
        if audio_files and len(audio_files) > 0:
            for i, audio_file in enumerate(audio_files):
                if audio_file and audio_file.filename:
                    audio_path_temp = temp_dir / f"audio_{task_id}_{i}{Path(audio_file.filename).suffix}"
                    with open(audio_path_temp, 'wb') as f:
                        content = await audio_file.read()
                        f.write(content)
                    audio_file_paths.append(audio_path_temp)
                    logger.info(f"[音视频合成] 音频文件 {i+1} 已上传: {audio_path_temp}")
        elif audio_path:
            audio_file_paths.append(Path(audio_path))

        if len(audio_file_paths) == 0:
            return JSONResponse({
                'success': False,
                'error': '未找到有效的音频文件'
            }, status_code=400)

        # 创建任务
        async def mux_task():
            try:
                TOOL_TASKS[task_id]['status'] = 'processing'
                TOOL_TASKS[task_id]['progress'] = 10
                TOOL_TASKS[task_id]['message'] = '正在准备文件...'

                TOOL_TASKS[task_id]['progress'] = 30
                TOOL_TASKS[task_id]['message'] = '视频文件准备完成'

                # 处理音频文件
                final_audio_path = None

                # 如果有多个音频文件，需要先混音
                if len(audio_file_paths) > 1:
                    TOOL_TASKS[task_id]['progress'] = 35
                    TOOL_TASKS[task_id]['message'] = f'正在混音 {len(audio_file_paths)} 个音频轨道...'
                    logger.info(f"[音视频合成] 开始混音 {len(audio_file_paths)} 个音频轨道")

                    # 构建ffmpeg混音命令
                    mixed_audio_path = temp_dir / f"mixed_audio_{task_id}.wav"

                    # 构建输入参数
                    input_args = []
                    for audio_path in audio_file_paths:
                        input_args.extend(['-i', str(audio_path)])

                    # 构建filter_complex参数：使用amix混音
                    filter_inputs = ''.join([f'[{i}:a]' for i in range(len(audio_file_paths))])
                    filter_complex = f'{filter_inputs}amix=inputs={len(audio_file_paths)}:duration=longest:dropout_transition=0[aout]'

                    mix_cmd = [
                        'ffmpeg', '-y',
                        *input_args,
                        '-filter_complex', filter_complex,
                        '-map', '[aout]',
                        '-ar', '48000',  # 采样率
                        '-ac', '2',      # 立体声
                        str(mixed_audio_path)
                    ]

                    logger.debug(f"[音视频合成] 混音命令: {' '.join(mix_cmd)}")

                    mix_result = subprocess.run(
                        mix_cmd,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='ignore'
                    )

                    if mix_result.returncode != 0:
                        logger.error(f"[音视频合成] 混音失败: {mix_result.stderr}")
                        raise Exception(f"音频混音失败: {mix_result.stderr[:200]}")

                    if not mixed_audio_path.exists():
                        raise Exception("混音后的音频文件未创建")

                    final_audio_path = mixed_audio_path
                    logger.info(f"[音视频合成] 音频混音完成: {mixed_audio_path}")
                else:
                    final_audio_path = audio_file_paths[0]
                    logger.info(f"[音视频合成] 使用单个音频文件: {final_audio_path}")

                TOOL_TASKS[task_id]['progress'] = 40
                TOOL_TASKS[task_id]['message'] = '音频文件准备完成'

                # 准备输出文件
                output_dir = Path('temp/muxed_videos').resolve()  # 转换为绝对路径
                output_dir.mkdir(parents=True, exist_ok=True)

                if not output_filename:
                    output_filename = f"muxed_{task_id}.mp4"

                output_path = output_dir / output_filename

                TOOL_TASKS[task_id]['progress'] = 50
                TOOL_TASKS[task_id]['message'] = '正在合成音视频...'

                # 构建ffmpeg命令
                # 使用与step7相同的参数
                cmd = [
                    'ffmpeg', '-y',
                    '-i', str(video_file_path),
                    '-i', str(final_audio_path),
                    '-map', '0:v',  # 取第一个输入的视频流
                    '-map', '1:a',  # 取第二个输入的音频流
                    '-c:v', 'copy',  # 视频不重新编码，直接复制
                    '-c:a', 'aac',   # 音频编码为AAC
                    '-b:a', '192k',  # 音频比特率192k
                    str(output_path)
                ]

                logger.info(f"[音视频合成] 执行ffmpeg命令...")
                logger.debug(f"[音视频合成] 命令: {' '.join(cmd)}")

                # 执行ffmpeg
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )

                if result.returncode != 0:
                    logger.error(f"[音视频合成] ffmpeg错误: {result.stderr}")
                    raise Exception(f"ffmpeg合成失败: {result.stderr[:200]}")

                if not output_path.exists():
                    raise Exception("合成后的视频文件未创建")

                # 获取文件大小
                file_size = output_path.stat().st_size
                file_size_mb = file_size / (1024 * 1024)

                TOOL_TASKS[task_id]['status'] = 'completed'
                TOOL_TASKS[task_id]['progress'] = 100
                TOOL_TASKS[task_id]['message'] = '音视频合成完成'
                TOOL_TASKS[task_id]['result'] = {
                    'video_path': str(output_path.relative_to(Path.cwd())),
                    'file_size': file_size,
                    'file_size_mb': round(file_size_mb, 2)
                }

                logger.info(f"[音视频合成] 完成: {output_path} ({file_size_mb:.2f}MB)")

            except Exception as e:
                logger.error(f"[音视频合成] 失败: {e}")
                TOOL_TASKS[task_id]['status'] = 'failed'
                TOOL_TASKS[task_id]['message'] = f'合成失败: {str(e)}'
                TOOL_TASKS[task_id]['result'] = {'error': str(e)}

        # 注册任务
        TOOL_TASKS[task_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '开始音视频合成...',
            'result': None
        }

        # 启动异步任务
        asyncio.create_task(mux_task())

        return JSONResponse({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'processing',
                'message': '开始音视频合成'
            }
        })

    except Exception as e:
        logger.error(f"[音视频合成] 启动失败: {e}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)
