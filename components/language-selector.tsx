'use client'

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useTranslation } from '@/hooks/useTranslation'
import { BrazilFlag, UKFlag, SpainFlag } from './flags'

const languages = [
  { code: 'pt-BR', name: 'Português', Flag: BrazilFlag },
  { code: 'en-US', name: 'English', Flag: UKFlag },
  { code: 'es-ES', name: 'Español', Flag: SpainFlag }
]

export function LanguageSelector() {
  const { currentLanguage, setLanguage } = useTranslation()

  const currentLang = languages.find(lang => lang.code === currentLanguage)
  const Flag = currentLang?.Flag || BrazilFlag

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
        >
          <Flag />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="bg-zinc-950 border-zinc-800">
        {languages.map((lang) => (
          <DropdownMenuItem
            key={lang.code}
            onClick={() => setLanguage(lang.code as LanguageType)}
            className={`
              cursor-pointer text-zinc-400 hover:text-emerald-400 hover:bg-zinc-900
              ${currentLanguage === lang.code ? 'text-emerald-400 bg-emerald-900/20' : ''}
            `}
          >
            <span className="flex items-center gap-2">
              <lang.Flag />
              {lang.name}
            </span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
