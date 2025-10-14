export type Locale = 'en' | 'zh'

export const locales: Locale[] = ['en', 'zh']

export const defaultLocale: Locale = 'zh'

export const localeNames: Record<Locale, string> = {
  en: 'English',
  zh: '中文',
}
