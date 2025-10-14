# TransVox 并发控制和多用户支持报告

## 📊 当前系统架构分析

### 1. 多用户支持 ✅

**支持情况：是**

系统通过以下机制支持多用户：

- **用户ID识别**：通过 `_get_user_id(request)` 从请求中获取用户ID
- **用户隔离**：
  - 输入文件：`input/{user_id}/{job_id}/`
  - 输出文件：`output/{user_id}/{job_id}/{video_stem}/`
- **权限验证**：停止任务时验证用户权限，防止跨用户操作

### 2. 并发控制机制

#### 当前实现

**全局并发限制：**
```python
RUNNING_JOB: Optional[dict] = None  # 当前运行的任务（全局只有1个）
JOB_QUEUE = deque()                 # 任务队列（FIFO）
CURRENT_RUNNING: Optional[str] = None  # 当前运行的任务ID
```

**工作流程：**
1. 新任务提交 → 检查用户是否已有活动任务
2. 如果有活动任务 → 返回409冲突
3. 如果没有 → 加入队列 `JOB_QUEUE`
4. 异步worker轮询：
   - 如果 `RUNNING_JOB is None` 且队列不为空
   - 从队列取出任务 → 设置为 `RUNNING_JOB`
   - 执行任务 → 完成后释放 `RUNNING_JOB`

#### 并发数控制

**全局并发数：1** （同时只能运行1个任务）

**按用户限制：每用户1个任务**
```python
def _user_has_active_job(user_id: str) -> Optional[str]:
    # 检查运行中的任务
    if RUNNING_JOB and RUNNING_JOB.get('user_id') == user_id:
        return RUNNING_JOB.get('job_id')
    # 检查队列中的任务
    for job in JOB_QUEUE:
        if job.get('user_id') == user_id:
            return job.get('job_id')
    return None
```

### 3. 进程管理

**当前实现：**
- 使用 `subprocess.Popen` 启动子进程
- 进程映射：`PROCESS_MAP[job_id] = proc`
- 支持取消任务（通过 `_kill_process_tree` 终止进程树）

**没有使用进程池**，而是：
- 单个worker异步处理队列
- 每个任务启动新的子进程

## 📈 系统限制

### 当前限制

1. **全局并发数：1**
   - ⚠️ 所有用户共享1个处理槽位
   - 如果A用户在处理，B用户必须等待

2. **用户并发数：1**
   - ✅ 防止单个用户提交多个任务占用资源
   - ⚠️ 用户无法同时处理多个视频

3. **队列管理：简单FIFO**
   - ✅ 先进先出，公平调度
   - ⚠️ 没有优先级机制
   - ⚠️ 没有超时清理

### 视频时长和文件大小限制

```python
MAX_VIDEO_BYTES = 2 * 1024 * 1024 * 1024  # 2GB
MAX_VIDEO_DURATION = 60 * 60  # 1小时
```

## 🎯 优化建议

### 方案A：增加全局并发数（简单）

**适用场景**：服务器资源充足，希望提高吞吐量

**实现方案**：
```python
MAX_CONCURRENT_JOBS = 3  # 可配置

RUNNING_JOBS = {}  # {job_id: job_dict}

async def _job_worker():
    while True:
        if len(RUNNING_JOBS) < MAX_CONCURRENT_JOBS and JOB_QUEUE:
            job = JOB_QUEUE.popleft()
            RUNNING_JOBS[job['job_id']] = job
            asyncio.create_task(execute_and_cleanup(job))
        await asyncio.sleep(0.3)
```

**优点**：
- 简单实现，改动小
- 提高系统吞吐量

**缺点**：
- 仍然是单worker模式
- 资源竞争可能导致OOM

### 方案B：用户级并发池（推荐）

**适用场景**：多用户环境，需要隔离和公平性

**实现方案**：
```python
MAX_JOBS_PER_USER = 2  # 每用户2个并发
MAX_GLOBAL_JOBS = 5     # 全局最多5个并发

USER_JOBS = defaultdict(set)  # {user_id: {job_id1, job_id2, ...}}
```

**优点**：
- 用户隔离，公平分配
- 防止单用户占用所有资源
- 提高多用户体验

**缺点**：
- 实现复杂度中等
- 需要更多内存管理

### 方案C：使用进程池（高级）

**适用场景**：高负载生产环境

**实现方案**：
```python
from concurrent.futures import ProcessPoolExecutor

executor = ProcessPoolExecutor(max_workers=4)

async def execute_job(job):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _execute_job_sync, job)
```

**优点**：
- 真正的并行处理
- 进程隔离，稳定性高
- 资源利用率高

**缺点**：
- 实现复杂，需要重构
- 进程间通信开销
- 内存占用增加

## 💡 配置化建议

建议添加配置文件支持：

```json
{
  "concurrency": {
    "max_global_jobs": 3,
    "max_jobs_per_user": 1,
    "queue_timeout": 3600,
    "enable_priority": false
  },
  "limits": {
    "max_video_size_mb": 2048,
    "max_video_duration_minutes": 60,
    "max_queue_size": 100
  }
}
```

## 📝 当前问题总结

1. ✅ **支持多用户**：用户隔离良好
2. ⚠️ **全局并发数为1**：吞吐量受限
3. ✅ **防止用户重复提交**：每用户限制1个任务
4. ⚠️ **没有进程池**：使用简单队列机制
5. ⚠️ **不支持配置并发数**：硬编码在代码中
6. ⚠️ **没有队列清理机制**：长时间排队的任务不会超时

## 🔧 快速改进建议（优先级排序）

1. **立即可做**：
   - 添加 `MAX_CONCURRENT_JOBS` 配置项
   - 修改为支持多个 `RUNNING_JOBS`

2. **短期改进**：
   - 添加队列超时清理
   - 添加任务优先级

3. **长期优化**：
   - 实现用户级并发池
   - 使用进程池管理

## 📊 性能估算

假设平均视频处理时间：10分钟

| 并发数 | 每小时吞吐量 | 10用户平均等待 |
|-------|------------|--------------|
| 1     | 6个视频     | ~50分钟      |
| 3     | 18个视频    | ~15分钟      |
| 5     | 30个视频    | ~10分钟      |

**建议配置**：
- 小型部署（单用户/开发）：1-2并发
- 中型部署（团队使用）：3-5并发
- 大型部署（公开服务）：5-10并发 + 进程池
