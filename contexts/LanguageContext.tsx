'use client'

import { createContext, useContext, useState, useCallback } from 'react'
import ptBR from '../locales/pt-BR'

type LanguageType = 'pt-BR'

const translations = {
  'pt-BR': ptBR
} as const

type LanguageContextType = {
  currentLanguage: LanguageType
  setLanguage: (lang: LanguageType) => void
  t: (key: string) => string
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [currentLanguage, setCurrentLanguage] = useState<LanguageType>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('language') as LanguageType || 'pt-BR'
    }
    return 'pt-BR'
  })

  const t = useCallback((key: string) => {
    const keys = key.split('.')
    let translation: any = translations[currentLanguage]
    
    for (const k of keys) {
      translation = translation[k]
      if (!translation) return key
    }
    
    return translation
  }, [currentLanguage])

  const handleSetLanguage = useCallback((lang: LanguageType) => {
    setCurrentLanguage(lang)
    if (typeof window !== 'undefined') {
      localStorage.setItem('language', lang)
    }
  }, [])

  return (
    <LanguageContext.Provider value={{
      currentLanguage,
      setLanguage: handleSetLanguage,
      t
    }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguageContext() {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguageContext must be used within a LanguageProvider')
  }
  return context
}