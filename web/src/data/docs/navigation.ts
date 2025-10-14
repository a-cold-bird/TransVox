import { DocSection } from '@/types/docs'

export const docsNavigation: DocSection[] = [
  {
    title: 'docs.sections.gettingStarted',
    items: [
      {
        title: 'docs.items.introduction',
        href: '/docs',
        icon: 'book',
      },
      {
        title: 'docs.items.installation',
        href: '/docs/installation',
        icon: 'download',
      },
      {
        title: 'docs.items.quickStart',
        href: '/docs/quick-start',
        icon: 'rocket',
      },
    ],
  },
  {
    title: 'docs.sections.features',
    items: [
      {
        title: 'docs.items.videoTranslation',
        href: '/docs/features/translation',
        icon: 'language',
      },
      {
        title: 'docs.items.voiceCloning',
        href: '/docs/features/voice-cloning',
        icon: 'microphone',
      },
      {
        title: 'docs.items.subtitleProcessing',
        href: '/docs/features/subtitles',
        icon: 'file-lines',
      },
      {
        title: 'docs.items.webTools',
        href: '/docs/features/web-tools',
        icon: 'wrench',
      },
    ],
  },
  {
    title: 'docs.sections.apiReference',
    items: [
      {
        title: 'docs.items.restApi',
        href: '/docs/api/rest',
        icon: 'code',
      },
      {
        title: 'docs.items.configuration',
        href: '/docs/api/configuration',
        icon: 'gear',
      },
    ],
  },
  {
    title: 'docs.sections.advanced',
    items: [
      {
        title: 'docs.items.customModels',
        href: '/docs/advanced/custom-models',
        icon: 'lightbulb',
      },
    ],
  },
]
