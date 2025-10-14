import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import '@fortawesome/fontawesome-svg-core/styles.css'
import '@/lib/fontawesome'
import { I18nProvider } from '@/components/I18nProvider'
import { Toaster } from '@/components/ui/toaster'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TransVox - AI Video Translation & Dubbing Platform',
  description: 'Professional video translation and dubbing with AI-powered voice cloning',
  keywords: ['video translation', 'AI dubbing', 'voice cloning', 'subtitle generation'],
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon.png', type: 'image/png' },
    ],
    apple: '/asset/icon.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  const appearance = localStorage.getItem('appearance') || 'dark';
                  const theme = 'blue-purple';
                  const html = document.documentElement;

                  html.classList.add('theme-' + theme);
                  if (appearance === 'dark') {
                    html.classList.add('dark');
                  }
                } catch (e) {
                  console.error('Failed to set theme:', e);
                }
              })();
            `,
          }}
        />
      </head>
      <body className={inter.className}>
        <I18nProvider>
          {children}
          <Toaster />
        </I18nProvider>
      </body>
    </html>
  )
}

