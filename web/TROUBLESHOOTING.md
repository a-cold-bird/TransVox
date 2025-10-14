# TransVox Web 故障排除指南

## 🔧 安装问题

### 问题 1: `tailwindcss-animate` 模块未找到

**错误信息：**
```
Error: Cannot find module 'tailwindcss-animate'
```

**解决方案：**
```bash
npm install tailwindcss-animate --save-dev
```

或者重新安装所有依赖：
```bash
rm -rf node_modules package-lock.json
npm install
```

### 问题 2: Nextra 相关错误

**错误信息：**
```
Cannot find module 'nextra'
```

**解决方案：**
```bash
npm install nextra nextra-theme-docs --save
```

### 问题 3: 依赖版本冲突

**解决方案：**
```bash
# 清除缓存
npm cache clean --force

# 删除并重新安装
rm -rf node_modules package-lock.json
npm install

# 或使用 legacy peer deps
npm install --legacy-peer-deps
```

## 🚀 运行时问题

### 问题 4: 端口 3000 被占用

**错误信息：**
```
Port 3000 is already in use
```

**解决方案：**
```bash
# 方法 1: 使用不同端口
PORT=3001 npm run dev

# 方法 2 (Windows): 找到并关闭占用进程
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# 方法 2 (Linux/Mac): 找到并关闭占用进程
lsof -ti:3000 | xargs kill -9
```

### 问题 5: API 连接失败

**错误信息：**
```
Network Error / Failed to fetch
```

**检查清单：**
1. 确认后端服务器正在运行：`http://localhost:8000`
2. 检查 `.env.local` 文件中的 `NEXT_PUBLIC_API_URL`
3. 检查防火墙设置
4. 尝试直接访问 API：`curl http://localhost:8000/api/health`

**解决方案：**
```bash
# 1. 检查后端是否运行
curl http://localhost:8000

# 2. 确认 .env.local 配置
cat .env.local

# 3. 重启前端服务器
npm run dev
```

### 问题 6: 类型错误

**错误信息：**
```
TypeScript error: ...
```

**解决方案：**
```bash
# 运行类型检查
npm run type-check

# 如果是临时问题，可以重启 TypeScript 服务器
# VS Code: Ctrl+Shift+P -> "TypeScript: Restart TS Server"
```

## 🎨 样式问题

### 问题 7: Tailwind 样式不生效

**解决方案：**
```bash
# 1. 确认 tailwind.config.ts 配置正确
# 2. 重启开发服务器
npm run dev

# 3. 清除 Next.js 缓存
rm -rf .next
npm run dev
```

### 问题 8: 深色模式不工作

**检查：**
1. 确认 `tailwind.config.ts` 中有 `darkMode: ['class']`
2. 检查 `globals.css` 中的 dark 主题变量
3. 确认组件使用了 `dark:` 前缀

## 📦 构建问题

### 问题 9: 构建失败

**错误信息：**
```
Build failed
```

**解决方案：**
```bash
# 1. 清除缓存
rm -rf .next node_modules

# 2. 重新安装依赖
npm install

# 3. 尝试构建
npm run build

# 4. 如果仍然失败，检查错误日志
npm run build 2>&1 | tee build.log
```

### 问题 10: 生产环境图片加载失败

**解决方案：**

在 `next.config.js` 中配置图片域名：
```javascript
images: {
  domains: ['localhost', 'your-api-domain.com'],
}
```

## 🔍 调试技巧

### 启用详细日志

```bash
# 开发模式详细日志
DEBUG=* npm run dev

# 检查构建信息
npm run build -- --profile
```

### 浏览器开发工具

1. **Network 面板**: 检查 API 请求和响应
2. **Console 面板**: 查看 JavaScript 错误
3. **React DevTools**: 检查组件状态
4. **Redux DevTools**: 检查 Zustand store（如果安装了扩展）

### 常用调试命令

```bash
# 检查 Node.js 版本
node --version

# 检查 npm 版本
npm --version

# 查看已安装的包
npm list --depth=0

# 检查过期的包
npm outdated

# 验证 package.json
npm doctor
```

## 📱 移动端问题

### 问题 11: 移动端布局错乱

**检查：**
1. 确认使用了响应式类（`sm:`, `md:`, `lg:`）
2. 检查 viewport meta 标签
3. 使用浏览器的移动设备模拟器测试

## 🌐 部署问题

### 问题 12: Vercel 部署失败

**常见原因：**
1. 环境变量未配置
2. 构建命令不正确
3. Node.js 版本不匹配

**解决方案：**
```bash
# 1. 本地测试生产构建
npm run build
npm start

# 2. 检查 .env.local 变量是否在 Vercel 中配置
# 3. 确认 package.json 中的 engines 字段
```

### 问题 13: API 跨域问题

**解决方案：**

在 `next.config.js` 中添加：
```javascript
async headers() {
  return [
    {
      source: '/api/:path*',
      headers: [
        { key: 'Access-Control-Allow-Origin', value: '*' },
        { key: 'Access-Control-Allow-Methods', value: 'GET,POST,PUT,DELETE' },
      ],
    },
  ]
}
```

## 🆘 获取帮助

如果以上方法都无法解决问题：

1. **查看日志**: 检查浏览器控制台和终端输出
2. **搜索错误**: 在 Google 或 Stack Overflow 搜索错误信息
3. **查看文档**: 
   - [Next.js 文档](https://nextjs.org/docs)
   - [React 文档](https://react.dev/)
   - [Tailwind CSS 文档](https://tailwindcss.com/docs)
4. **提交 Issue**: 在 GitHub 仓库提交详细的错误报告

## ✅ 验证清单

运行以下命令确保一切正常：

```bash
# 1. 依赖安装
npm install

# 2. 类型检查
npm run type-check

# 3. 代码检查
npm run lint

# 4. 开发服务器
npm run dev

# 5. 生产构建
npm run build
npm start
```

如果所有步骤都成功，说明环境配置正确！

## 📞 联系支持

- GitHub Issues: [项目地址]/issues
- 文档: http://localhost:3000/docs
- Email: support@transvox.com


