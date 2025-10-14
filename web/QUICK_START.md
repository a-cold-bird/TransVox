# TransVox Web 快速启动指南

## 📦 安装步骤

### 1. 安装依赖

```bash
cd web
npm install
```

如果使用 yarn 或 pnpm：

```bash
yarn install
# 或
pnpm install
```

### 2. 配置环境变量

创建 `.env.local` 文件：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000)

## 🚀 功能特性

### ✅ 已实现的功能

1. **视频上传**
   - 拖拽上传
   - 进度显示
   - 文件类型验证

2. **流水线配置**
   - 语言选择（中/英/日/韩）
   - TTS引擎选择（GPT-SoVITS/IndexTTS）
   - 字幕嵌入模式（硬编码/软字幕/外挂/混合）

3. **实时进度追踪**
   - 步骤可视化
   - 进度百分比
   - 状态更新

4. **文档系统**
   - 基于 Nextra 的文档
   - 安装指南
   - API 参考

### 🎨 UI 组件

基于 Radix UI 的完整组件库：

- Button
- Card
- Progress
- Select
- Toast
- Dialog
- 等等...

## 📁 项目结构

```
web/
├── src/
│   ├── app/              # 页面
│   │   ├── page.tsx      # 首页
│   │   ├── workspace/    # 工作空间
│   │   └── globals.css   # 全局样式
│   ├── components/       # 组件
│   │   ├── ui/          # 基础UI组件
│   │   ├── video/       # 视频相关
│   │   └── pipeline/    # 流水线组件
│   ├── api/             # API 客户端
│   ├── store/           # 状态管理
│   ├── types/           # 类型定义
│   └── pages/           # 文档页面
├── package.json
├── tsconfig.json
└── tailwind.config.ts
```

## 🔌 API 集成

前端通过以下服务与后端通信：

```typescript
import { 
  videoService, 
  pipelineService, 
  subtitleService 
} from '@/api/services'

// 上传视频
await videoService.uploadVideo(file)

// 启动流水线
await pipelineService.startPipeline(config)

// 嵌入字幕
await subtitleService.embedSubtitle(config)
```

## 🎯 使用流程

### 1. 上传视频

在工作空间页面拖拽视频文件或点击选择文件。

### 2. 配置流水线

选择：
- 源语言
- 目标语言
- TTS 引擎
- 字幕嵌入模式

### 3. 启动处理

点击 "Start Pipeline" 开始处理。

### 4. 查看进度

实时查看处理进度和当前步骤。

### 5. 下载结果

处理完成后下载翻译好的视频。

## 🛠️ 开发命令

```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 启动生产服务器
npm start

# 类型检查
npm run type-check

# 代码检查
npm run lint
```

## 🎨 主题定制

修改 `tailwind.config.ts` 中的颜色配置：

```typescript
colors: {
  primary: {
    DEFAULT: 'hsl(221.2 83.2% 53.3%)',
    foreground: 'hsl(210 40% 98%)',
  },
  // ... 其他颜色
}
```

## 📚 技术栈详情

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 14.2.13 | React 框架 |
| React | 18.3.1 | UI 库 |
| TypeScript | 5.6.2 | 类型系统 |
| Tailwind CSS | 3.4.13 | 样式框架 |
| Radix UI | Latest | 无障碍组件 |
| Framer Motion | 11.6.0 | 动画库 |
| Zustand | 4.5.5 | 状态管理 |
| Axios | 1.7.7 | HTTP 客户端 |
| Nextra | 2.13.4 | 文档系统 |

## 🐛 故障排除

### 端口被占用

如果 3000 端口被占用，修改启动命令：

```bash
PORT=3001 npm run dev
```

### API 连接失败

确保后端服务器在 `http://localhost:8000` 运行。

检查 `.env.local` 中的 `NEXT_PUBLIC_API_URL` 配置。

### 依赖安装失败

清除缓存后重试：

```bash
rm -rf node_modules package-lock.json
npm install
```

## 📖 更多资源

- [完整文档](http://localhost:3000/docs)
- [API 参考](http://localhost:3000/docs/api)
- [组件示例](http://localhost:3000/docs/components)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可

与主项目相同的许可证。

