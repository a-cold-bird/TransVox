# TransVox Web 完整安装指南

## 📋 前置要求

### 必需软件

- **Node.js**: 18.0.0 或更高版本
  - 下载: https://nodejs.org/
  - 验证: `node --version`
  
- **npm**: 9.0.0 或更高版本（通常随 Node.js 安装）
  - 验证: `npm --version`

- **Git**: 用于克隆仓库（可选）
  - 下载: https://git-scm.com/

### 推荐软件

- **VS Code**: 推荐的代码编辑器
- **Cursor**: AI 辅助编程工具

## 🚀 安装步骤

### 方法 1: 自动安装（推荐）

#### Windows:
```bash
cd web
.\install.bat
```

#### Linux/macOS:
```bash
cd web
chmod +x install.sh
./install.sh
```

### 方法 2: 手动安装

#### 步骤 1: 进入项目目录
```bash
cd web
```

#### 步骤 2: 安装依赖
```bash
npm install
```

如果遇到依赖冲突：
```bash
npm install --legacy-peer-deps
```

#### 步骤 3: 创建环境配置
```bash
# Windows
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local

# Linux/macOS
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

#### 步骤 4: 验证安装
```bash
npm run type-check
```

## ✅ 安装验证

### 运行测试脚本

#### Windows:
```bash
.\test-setup.bat
```

#### Linux/macOS:
```bash
chmod +x test-setup.sh
./test-setup.sh
```

### 手动验证

```bash
# 1. 检查依赖
npm list --depth=0

# 2. 类型检查
npm run type-check

# 3. 代码检查
npm run lint

# 4. 尝试构建
npm run build
```

## 🎯 启动应用

### 开发模式

```bash
npm run dev
```

应用将在 http://localhost:3000 启动

### 生产模式

```bash
# 构建
npm run build

# 启动
npm start
```

## 🔧 常见问题修复

### 问题 1: `tailwindcss-animate` 未找到

```bash
npm install tailwindcss-animate --save-dev
```

### 问题 2: 端口被占用

```bash
# 使用不同端口
PORT=3001 npm run dev
```

### 问题 3: 依赖安装失败

```bash
# 清除缓存
npm cache clean --force

# 删除 node_modules
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

### 问题 4: TypeScript 错误

```bash
# 重新生成类型
rm -rf .next
npm run dev
```

### 问题 5: Nextra 配置错误

Nextra 是可选的文档系统，如果遇到问题可以：

```bash
npm install nextra nextra-theme-docs --save
```

或者临时禁用 Nextra（项目会正常运行，只是没有 `/docs` 路由）。

## 📦 依赖说明

### 核心依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| next | 14.2.13 | React 框架 |
| react | 18.3.1 | UI 库 |
| typescript | 5.6.2 | 类型系统 |
| tailwindcss | 3.4.13 | CSS 框架 |

### UI 组件

| 包名 | 用途 |
|------|------|
| @radix-ui/* | 无障碍 UI 组件 |
| framer-motion | 动画库 |
| lucide-react | 图标库 |

### 工具库

| 包名 | 用途 |
|------|------|
| axios | HTTP 客户端 |
| zustand | 状态管理 |
| react-dropzone | 文件上传 |

### 开发工具

| 包名 | 用途 |
|------|------|
| eslint | 代码检查 |
| tailwindcss-animate | Tailwind 动画 |

## 🌐 环境变量配置

在 `.env.local` 文件中配置：

```env
# API 地址（必需）
NEXT_PUBLIC_API_URL=http://localhost:8000

# 可选配置
# NEXT_PUBLIC_AUTH_ENABLED=false
# NEXT_PUBLIC_GA_ID=your-google-analytics-id
```

## 📁 项目结构验证

确保以下文件存在：

```
web/
├── package.json          ✓ 依赖配置
├── tsconfig.json         ✓ TypeScript 配置
├── next.config.js        ✓ Next.js 配置
├── tailwind.config.ts    ✓ Tailwind 配置
├── postcss.config.js     ✓ PostCSS 配置
├── .eslintrc.json        ✓ ESLint 配置
├── theme.config.tsx      ✓ Nextra 主题
├── .env.local            ✓ 环境变量
└── src/
    ├── app/              ✓ 页面
    ├── components/       ✓ 组件
    ├── lib/              ✓ 工具
    ├── api/              ✓ API 客户端
    ├── store/            ✓ 状态管理
    └── types/            ✓ 类型定义
```

## 🔍 故障排除

### 调试模式

```bash
# 启用详细日志
DEBUG=* npm run dev

# 查看构建详情
npm run build -- --profile
```

### 清除缓存

```bash
# 清除 Next.js 缓存
rm -rf .next

# 清除所有缓存并重新安装
npm run clean
npm install
```

### 检查系统状态

```bash
# Node.js 版本
node --version

# npm 版本
npm --version

# 检查过期包
npm outdated

# 检查系统健康
npm doctor
```

## 📞 获取帮助

如果遇到问题：

1. **查看错误日志**: 检查终端输出和浏览器控制台
2. **阅读文档**: 
   - 本地文档: http://localhost:3000/docs
   - Next.js: https://nextjs.org/docs
3. **查看故障排除**: 参考 `TROUBLESHOOTING.md`
4. **提交 Issue**: 在 GitHub 仓库提交问题

## ✅ 安装成功标志

如果看到以下输出，说明安装成功：

```bash
npm run dev

> transvox-web@1.0.0 dev
> next dev

- ready started server on 0.0.0.0:3000, url: http://localhost:3000
- event compiled client and server successfully
- wait compiling...
```

访问 http://localhost:3000 应该能看到 TransVox 首页。

## 🎓 下一步

安装完成后：

1. 阅读 [QUICK_START.md](./QUICK_START.md) 快速开始
2. 查看 [README.md](./README.md) 了解功能
3. 访问 http://localhost:3000/docs 查看文档
4. 开始使用 TransVox！

---

**祝您使用愉快！** 🎉


