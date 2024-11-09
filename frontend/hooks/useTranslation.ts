import { translations } from '@/lib/translations'
import { useLanguage } from '@/contexts/LanguageContext'

type TranslationsType = typeof translations.en

type PathsToStringProps<T> = T extends string
  ? never
  : T extends object
  ? {
      [K in keyof T]: T[K] extends object
        ? `${K & string}.${PathsToStringProps<T[K]>}`
        : K & string
    }[keyof T]
  : never

export type TranslationKey = PathsToStringProps<TranslationsType>

export function useTranslation() {
  const { language, changeLanguage } = useLanguage()

  const t = (key: TranslationKey | string) => {
    const keys = key.split('.')
    let value: any = translations[language]
    
    for (const k of keys) {
      if (value[k] === undefined) return key
      value = value[k]
    }
    
    return value as string
  }

  return { t, language, changeLanguage }
} 