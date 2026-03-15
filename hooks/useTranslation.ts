'use client'

import { useCallback } from 'react'
import { useLanguageContext } from '@/contexts/LanguageContext'

type LanguageType = 'pt-BR' | 'en-US' | 'es-ES'

export function useTranslation() {
  const { currentLanguage, setLanguage, t } = useLanguageContext()

  const handleLanguageChange = useCallback((lang: LanguageType) => {
    setLanguage(lang)
  }, [setLanguage])

  return { 
    t, 
    currentLanguage, 
    setLanguage: handleLanguageChange 
  }
}