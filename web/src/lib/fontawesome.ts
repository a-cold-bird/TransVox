/**
 * Font Awesome 图标库配置
 * 统一管理整个应用的图标
 */

import { library } from '@fortawesome/fontawesome-svg-core'
import { config } from '@fortawesome/fontawesome-svg-core'

// 导入 Solid 图标
import {
  faPlay,
  faPause,
  faUpload,
  faDownload,
  faVideo,
  faFileAudio,
  faFileVideo,
  faFileLines,
  faVolumeHigh,
  faScissors,
  faHeadphones,
  faEye,
  faCircleCheck,
  faCircleXmark,
  faClock,
  faCircleExclamation,
  faCircleQuestion,
  faSpinner,
  faFilm,
  faFont,
  faXmark,
  faLayerGroup,
  faCodeMerge,
  faArrowsRotate,
  faLanguage,
  faMusic,
  faMicrophone,
  faGlobe,
  faRocket,
  faBolt,
  faWandMagicSparkles,
  faChartLine,
  faShieldHalved,
  faGear,
  faWrench,
  faArrowRight,
  faArrowLeft,
  faStar,
  faHeart,
  faShareNodes,
  faBook,
  faBookOpen,
  faCirclePlay,
  faGraduationCap,
  faLightbulb,
  faCode,
  faServer,
  faDatabase,
  faCube,
  faCircleNodes,
  faCheck,
  faBars,
  faChevronRight,
  faChevronLeft,
  faChevronDown,
  faChevronUp,
  faPlus,
  faMinus,
  faTrash,
  faPen,
  faSave,
  faFolder,
  faFile,
  faFileCode,
  faSearch,
  faFilter,
  faSort,
  faEllipsisVertical,
  faBullseye,
  faSliders,
  faCircleInfo,
  faTriangleExclamation,
} from '@fortawesome/free-solid-svg-icons'

// 导入 Regular 图标
import {
  faFile as faFileRegular,
  faFolder as faFolderRegular,
  faHeart as faHeartRegular,
  faStar as faStarRegular,
  faCircle as faCircleRegular,
} from '@fortawesome/free-regular-svg-icons'

// 导入 Brands 图标
import {
  faGithub,
  faTwitter,
  faDiscord,
  faYoutube,
} from '@fortawesome/free-brands-svg-icons'

// 配置 Font Awesome
// 禁用自动添加 CSS（Next.js 使用 CSS-in-JS）
config.autoAddCss = false

// 注册所有图标到库中
library.add(
  // Solid 图标
  faPlay,
  faPause,
  faUpload,
  faDownload,
  faVideo,
  faFileAudio,
  faFileVideo,
  faFileLines,
  faVolumeHigh,
  faScissors,
  faHeadphones,
  faEye,
  faCircleCheck,
  faCircleXmark,
  faClock,
  faCircleExclamation,
  faCircleQuestion,
  faSpinner,
  faFilm,
  faFont,
  faXmark,
  faLayerGroup,
  faCodeMerge,
  faArrowsRotate,
  faLanguage,
  faMusic,
  faMicrophone,
  faGlobe,
  faRocket,
  faBolt,
  faWandMagicSparkles,
  faChartLine,
  faShieldHalved,
  faGear,
  faWrench,
  faArrowRight,
  faArrowLeft,
  faStar,
  faHeart,
  faShareNodes,
  faBook,
  faBookOpen,
  faCirclePlay,
  faGraduationCap,
  faLightbulb,
  faCode,
  faServer,
  faDatabase,
  faCube,
  faCircleNodes,
  faCheck,
  faBars,
  faChevronRight,
  faChevronLeft,
  faChevronDown,
  faChevronUp,
  faPlus,
  faMinus,
  faTrash,
  faPen,
  faSave,
  faFolder,
  faFile,
  faFileCode,
  faSearch,
  faFilter,
  faSort,
  faEllipsisVertical,
  faBullseye,
  faSliders,
  faCircleInfo,
  faTriangleExclamation,

  // Regular 图标
  faFileRegular,
  faFolderRegular,
  faHeartRegular,
  faStarRegular,
  faCircleRegular,

  // Brands 图标
  faGithub,
  faTwitter,
  faDiscord,
  faYoutube
)

/**
 * 图标名称映射表
 * 将常用的 lucide 图标名映射到 Font Awesome 图标
 */
export const iconMap = {
  // 媒体控制
  Play: 'play',
  Pause: 'pause',
  Volume2: 'volume-high',
  VolumeHigh: 'volume-high',

  // 文件相关
  Upload: 'upload',
  Download: 'download',
  FileVideo: 'file-video',
  FileAudio: 'file-audio',
  FileText: 'file-lines',
  File: 'file',
  Folder: 'folder',

  // 工具
  Scissors: 'scissors',
  Headphones: 'headphones',
  Eye: 'eye',
  RefreshCw: 'arrows-rotate',
  Refresh: 'arrows-rotate',

  // 状态
  CheckCircle: 'circle-check',
  XCircle: 'circle-xmark',
  Clock: 'clock',
  AlertCircle: 'circle-exclamation',
  Loader2: 'spinner',
  Spinner: 'spinner',

  // 媒体
  Film: 'film',
  Video: 'video',
  Type: 'font',
  Music: 'music',
  Microphone: 'microphone',
  Mic: 'microphone',

  // 操作
  X: 'xmark',
  Xmark: 'xmark',
  Layers: 'layer-group',
  Merge: 'code-merge',
  Language: 'language',
  Languages: 'language',

  // 特效
  Zap: 'bolt',
  Bolt: 'bolt',
  Sparkles: 'wand-magic-sparkles',
  WandMagicSparkles: 'wand-magic-sparkles',

  // 导航
  ArrowRight: 'arrow-right',
  ArrowLeft: 'arrow-left',
  ChevronRight: 'chevron-right',
  ChevronLeft: 'chevron-left',
  ChevronDown: 'chevron-down',
  ChevronUp: 'chevron-up',

  // 其他
  Globe: 'globe',
  Rocket: 'rocket',
  ChartLine: 'chart-line',
  Shield: 'shield-halved',
  Gear: 'gear',
  Settings: 'gear',
  Wrench: 'wrench',
  Star: 'star',
  Heart: 'heart',
  Share: 'share-nodes',
  BookOpen: 'book-open',
  Book: 'book',
  GraduationCap: 'graduation-cap',
  Lightbulb: 'lightbulb',
  Light: 'lightbulb',
  Code: 'code',
  Server: 'server',
  Database: 'database',
  Cube: 'cube',
  CircleNodes: 'circle-nodes',
  Check: 'check',
  CheckCircle2: 'circle-check',
  Times: 'xmark',
  Bars: 'bars',
  Plus: 'plus',
  Minus: 'minus',
  Trash: 'trash',
  Edit: 'pen',
  Save: 'save',
  Search: 'search',
  Filter: 'filter',
  Sort: 'sort',
  EllipsisVertical: 'ellipsis-vertical',
  Bullseye: 'bullseye',
  Sliders: 'sliders',
  HelpCircle: 'circle-question',
  Info: 'circle-info',
  AlertTriangle: 'triangle-exclamation',
  FileCode: 'file-code',
} as const

/**
 * 获取 Font Awesome 图标名称
 * @param iconName - Lucide 风格的图标名称
 * @returns Font Awesome 图标名称
 */
export function getFAIcon(iconName: keyof typeof iconMap | string): string {
  return iconMap[iconName as keyof typeof iconMap] || iconName.toLowerCase()
}
