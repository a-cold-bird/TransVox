#!/bin/bash

# TransVox 启动脚本 (Linux)
# 用于同时启动后端API服务器和前端开发服务器

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印欢迎信息
print_banner() {
    echo -e "${GREEN}"
    echo "======================================"
    echo "     TransVox 启动脚本"
    echo "======================================"
    echo -e "${NC}"
}

# 检查Python环境
check_python() {
    log_info "检查 Python 环境..."

    if ! command -v python3 &> /dev/null; then
        log_error "未找到 Python3，请先安装 Python 3.10+"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
    log_success "Python 版本: $PYTHON_VERSION"
}

# 检查虚拟环境
check_venv() {
    log_info "检查虚拟环境..."

    if [ ! -d "venv" ]; then
        log_warning "未找到虚拟环境，正在创建..."
        python3 -m venv venv
        log_success "虚拟环境创建完成"
    else
        log_success "虚拟环境已存在"
    fi
}

# 检查Node.js环境
check_node() {
    log_info "检查 Node.js 环境..."

    if ! command -v node &> /dev/null; then
        log_error "未找到 Node.js，请先安装 Node.js 18+"
        exit 1
    fi

    NODE_VERSION=$(node --version)
    log_success "Node.js 版本: $NODE_VERSION"
}

# 检查前端依赖
check_frontend_deps() {
    log_info "检查前端依赖..."

    if [ ! -d "web/node_modules" ]; then
        log_warning "前端依赖未安装，正在安装..."
        cd web
        npm install
        cd ..
        log_success "前端依赖安装完成"
    else
        log_success "前端依赖已安装"
    fi
}

# 检查环境变量
check_env() {
    log_info "检查环境变量..."

    if [ ! -f ".env" ]; then
        log_warning "未找到 .env 文件"
        if [ -f ".env_template" ]; then
            log_info "请根据 .env_template 创建 .env 文件并配置 API 密钥"
        fi
    else
        log_success ".env 文件已存在"
    fi
}

# 检查端口占用
check_port() {
    local port=$1
    local service=$2

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "$service 端口 $port 已被占用"
        read -p "是否要停止占用该端口的进程？(y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "正在停止端口 $port 的进程..."
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
            sleep 1
            log_success "端口 $port 已释放"
        else
            log_error "端口冲突，无法启动服务"
            return 1
        fi
    fi
    return 0
}

# 启动后端服务
start_backend() {
    log_info "启动后端 API 服务器..."

    # 检查端口
    if ! check_port 8000 "后端API"; then
        return 1
    fi

    # 激活虚拟环境并启动
    source venv/bin/activate

    # 检查 uvicorn 是否安装
    if ! python3 -c "import uvicorn" 2>/dev/null; then
        log_error "uvicorn 未安装，请运行: pip install -r requirements.txt"
        return 1
    fi

    # 启动后端
    log_info "后端服务启动中... (http://localhost:8000)"
    nohup python3 -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > .backend.pid

    # 等待后端启动
    sleep 3

    # 检查后端是否成功启动
    if kill -0 $BACKEND_PID 2>/dev/null; then
        log_success "后端服务启动成功 (PID: $BACKEND_PID)"
        log_info "后端日志: logs/backend.log"
        log_info "API 文档: http://localhost:8000/docs"
        return 0
    else
        log_error "后端服务启动失败，请查看日志: logs/backend.log"
        return 1
    fi
}

# 启动前端服务
start_frontend() {
    log_info "启动前端开发服务器..."

    # 检查端口
    if ! check_port 3000 "前端服务"; then
        return 1
    fi

    cd web

    # 启动前端
    log_info "前端服务启动中... (http://localhost:3000)"
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    echo $FRONTEND_PID > .frontend.pid

    # 等待前端启动
    sleep 5

    # 检查前端是否成功启动
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        log_success "前端服务启动成功 (PID: $FRONTEND_PID)"
        log_info "前端日志: logs/frontend.log"
        log_info "Web 界面: http://localhost:3000"
        log_info "在线文档: http://localhost:3000/docs"
        return 0
    else
        log_error "前端服务启动失败，请查看日志: logs/frontend.log"
        return 1
    fi
}

# 创建日志目录
create_log_dir() {
    if [ ! -d "logs" ]; then
        mkdir -p logs
        log_info "创建日志目录: logs/"
    fi
}

# 清理函数
cleanup() {
    log_info "正在清理..."

    # 停止后端
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            log_info "停止后端服务 (PID: $BACKEND_PID)..."
            kill $BACKEND_PID
        fi
        rm .backend.pid
    fi

    # 停止前端
    if [ -f ".frontend.pid" ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            log_info "停止前端服务 (PID: $FRONTEND_PID)..."
            kill $FRONTEND_PID
        fi
        rm .frontend.pid
    fi

    log_success "服务已停止"
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    print_banner

    # 创建日志目录
    create_log_dir

    # 环境检查
    check_python
    check_venv
    check_node
    check_frontend_deps
    check_env

    echo ""
    log_info "========== 启动服务 =========="
    echo ""

    # 启动后端
    if ! start_backend; then
        log_error "后端启动失败，退出"
        exit 1
    fi

    echo ""

    # 启动前端
    if ! start_frontend; then
        log_error "前端启动失败，正在停止后端..."
        cleanup
        exit 1
    fi

    echo ""
    echo -e "${GREEN}======================================"
    echo "     TransVox 启动完成！"
    echo "======================================"
    echo ""
    echo "访问地址:"
    echo "  Web 界面:  http://localhost:3000"
    echo "  在线文档:  http://localhost:3000/docs"
    echo "  API 文档:  http://localhost:8000/docs"
    echo ""
    echo "日志文件:"
    echo "  后端日志:  logs/backend.log"
    echo "  前端日志:  logs/frontend.log"
    echo ""
    echo -e "按 ${RED}Ctrl+C${GREEN} 停止所有服务"
    echo -e "======================================${NC}"
    echo ""

    # 保持脚本运行
    wait
}

# 执行主函数
main
