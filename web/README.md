# TransVox Web Frontend

Modern web interface for TransVox - AI-Powered Video Translation & Dubbing Platform.

## Tech Stack

- **Framework**: Next.js 14.2.13 + React 18.3.1
- **Documentation**: Nextra 2.13.4
- **Styling**: Tailwind CSS 3.4.13
- **UI Components**: Radix UI + Custom Components
- **Animation**: Framer Motion 11.6.0
- **Icons**: Lucide React + Radix Icons
- **Type System**: TypeScript 5.6.2
- **State Management**: Zustand 4.5.5
- **HTTP Client**: Axios 1.7.7

## Features

### Modern UI/UX

- Beautiful, responsive design
- Dark/Light mode support
- Smooth animations with Framer Motion
- Accessible components based on Radix UI

### Real-time Progress

- Live pipeline progress tracking
- Step-by-step visual feedback
- WebSocket updates (coming soon)

### Complete Configuration

- Easy-to-use pipeline configuration
- Multiple language support
- TTS engine selection
- Subtitle embedding modes

### Comprehensive Documentation

- Built-in documentation with Nextra
- Interactive examples
- API reference
- Troubleshooting guides

## Quick Start

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
npm run build
npm start
```

## Project Structure

```
web/
├── src/
│   ├── app/              # Next.js App Router pages
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Homepage
│   │   ├── workspace/    # Workspace pages
│   │   └── globals.css   # Global styles
│   ├── components/       # React components
│   │   ├── ui/          # Base UI components (Radix)
│   │   ├── video/       # Video-related components
│   │   └── pipeline/    # Pipeline components
│   ├── lib/             # Utilities
│   ├── api/             # API client & services
│   ├── store/           # Zustand stores
│   ├── types/           # TypeScript types
│   └── pages/           # Documentation pages
├── public/              # Static assets
├── next.config.js       # Next.js configuration
├── tailwind.config.ts   # Tailwind CSS configuration
├── tsconfig.json        # TypeScript configuration
└── package.json         # Dependencies
```

## Key Components

### VideoUpload

Drag-and-drop video upload with progress tracking.

```tsx
import { VideoUpload } from '@/components/video/VideoUpload'

<VideoUpload />
```

### PipelineConfig

Configuration panel for the translation pipeline.

```tsx
import { PipelineConfig } from '@/components/pipeline/PipelineConfig'

<PipelineConfig 
  videoPath="/path/to/video.mp4"
  onStart={(config) => console.log(config)}
/>
```

## API Integration

The frontend communicates with the backend API at `http://localhost:8000`.

### Services

```typescript
import { videoService, pipelineService } from '@/api/services'

// Upload video
await videoService.uploadVideo(file, (progress) => {
  console.log(`Upload progress: ${progress}%`)
})

// Start pipeline
await pipelineService.startPipeline(config)
```

### State Management

```typescript
import { useAppStore } from '@/store/useAppStore'

const { currentVideo, setCurrentVideo } = useAppStore()
```

## Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Documentation

Built-in documentation is powered by Nextra and can be accessed at `/docs`.

To add new documentation pages, create `.mdx` files in `src/pages/docs/`.

## Development

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

### Hot Reload

The development server supports hot module replacement for instant updates.

## Deployment

### Vercel (Recommended)

```bash
vercel
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### Static Export

```bash
npm run build
# Output in .next folder
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

See [LICENSE](../LICENSE) in the project root.

## Support

- Documentation: [http://localhost:3000/docs](http://localhost:3000/docs)
- Issues: [GitHub Issues](https://github.com/yourusername/transvox/issues)


