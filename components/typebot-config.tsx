'use client'

import { useState } from 'react'
import { useTranslation } from '@/hooks/useTranslation'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Bot } from 'lucide-react'

interface TypebotConfigProps {
  onSubmit: (config: { url: string; typebot: string }) => void
  onClose: () => void
}

export function TypebotConfig({ onSubmit, onClose }: TypebotConfigProps) {
  const { t } = useTranslation()
  const [config, setConfig] = useState({
    url: '',
    typebot: ''
  })
  const [errors, setErrors] = useState({
    url: '',
    typebot: ''
  })

  const validateUrl = (url: string) => {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  const handleUrlChange = (value: string) => {
    setConfig(prev => ({ ...prev, url: value }))
    
    if (!value) {
      setErrors(prev => ({ ...prev, url: 'URL é obrigatória' }))
    } else if (!validateUrl(value)) {
      setErrors(prev => ({ ...prev, url: 'Por favor, insira uma URL válida' }))
    } else {
      setErrors(prev => ({ ...prev, url: '' }))
    }
  }

  const handleTypebotChange = (value: string) => {
    setConfig(prev => ({ ...prev, typebot: value }))
    
    if (!value) {
      setErrors(prev => ({ ...prev, typebot: 'ID do Fluxo é obrigatório' }))
    } else {
      setErrors(prev => ({ ...prev, typebot: '' }))
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!errors.url && !errors.typebot && config.url && config.typebot) {
      onSubmit(config)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-md bg-zinc-950 border-zinc-900">
        <CardHeader className="border-b border-zinc-900 pb-4">
          <CardTitle className="text-xl font-bold text-zinc-100 flex items-center">
            <Bot className="mr-2 text-emerald-500 h-5 w-5" />
            {t('message_composition.form.typebot.title')}
          </CardTitle>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="pt-4 space-y-4">
            <div>
              <Label htmlFor="url" className="text-zinc-300">
                {t('message_composition.form.typebot.url.label')}
              </Label>
              <Input
                id="url"
                value={config.url}
                onChange={(e) => handleUrlChange(e.target.value)}
                className={`mt-1 bg-zinc-900 border-zinc-800 text-zinc-100 ${
                  errors.url ? 'border-red-500 focus-visible:ring-red-500' : ''
                }`}
                placeholder={t('message_composition.form.typebot.url.placeholder')}
                required
                onBlur={() => handleUrlChange(config.url)}
              />
              {errors.url && (
                <p className="text-red-500 text-sm mt-1">
                  {t('message_composition.form.typebot.url.error')}
                </p>
              )}
            </div>
            <div>
              <Label htmlFor="typebot" className="text-zinc-300">
                {t('message_composition.form.typebot.flow.label')}
              </Label>
              <Input
                id="typebot"
                value={config.typebot}
                onChange={(e) => handleTypebotChange(e.target.value)}
                className={`mt-1 bg-zinc-900 border-zinc-800 text-zinc-100 ${
                  errors.typebot ? 'border-red-500 focus-visible:ring-red-500' : ''
                }`}
                placeholder={t('message_composition.form.typebot.flow.placeholder')}
                required
                onBlur={() => handleTypebotChange(config.typebot)}
              />
              {errors.typebot && (
                <p className="text-red-500 text-sm mt-1">
                  {t('message_composition.form.typebot.flow.error')}
                </p>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex justify-end gap-2 border-t border-zinc-900 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="bg-zinc-900 border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-white"
            >
              {t('message_composition.form.typebot.buttons.cancel')}
            </Button>
            <Button
              type="submit"
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              {t('message_composition.form.typebot.buttons.save')}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
