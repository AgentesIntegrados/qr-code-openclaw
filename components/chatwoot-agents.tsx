import dynamic from 'next/dynamic'
import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Check, X } from "lucide-react"
import { useTranslation } from '@/hooks/useTranslation'

interface Agent {
  id: string
  name: string
}

interface AgentsConfigProps {
  agents: Agent[]
  selectedAgents: Agent[]
  onSubmit: (agents: Agent[]) => void
  onClose: () => void
}

export function AgentsConfig({ 
  agents = [],
  selectedAgents = [],
  onSubmit, 
  onClose 
}: AgentsConfigProps) {
  const { t } = useTranslation()
  const [localSelectedAgents, setLocalSelectedAgents] = useState<Agent[]>(selectedAgents)

  const handleToggleAgent = (agent: Agent) => {
    setLocalSelectedAgents(prev => {
      const isSelected = prev.some(a => a.id === agent.id)
      if (isSelected) {
        return prev.filter(a => a.id !== agent.id)
      }
      return [...prev, agent]
    })
  }

  const handleSubmit = () => {
    onSubmit(localSelectedAgents)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <Card 
        className="w-full max-w-md bg-zinc-950 border-zinc-900 shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-zinc-100">
              {t('message_composition.form.agents.title')}
            </h3>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-8 w-8 rounded-sm text-zinc-400 hover:bg-emerald-900/20 hover:text-emerald-400 transition-colors duration-200"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {agents && agents.length > 0 ? (
              agents.map(agent => (
                <div
                  key={agent.id}
                  onClick={() => handleToggleAgent(agent)}
                  className={`
                    flex items-center justify-between p-3 rounded-md cursor-pointer
                    ${localSelectedAgents.some(a => a.id === agent.id)
                      ? 'bg-emerald-900/20 border border-emerald-500/30 text-emerald-400'
                      : 'bg-zinc-900 border border-zinc-800 text-zinc-400 hover:border-zinc-700'
                    }
                  `}
                >
                  <span>{agent.name}</span>
                  {localSelectedAgents.some(a => a.id === agent.id) && (
                    <Check className="h-4 w-4" />
                  )}
                </div>
              ))
            ) : (
              <div className="text-center text-zinc-500 py-4">
                {t('message_composition.form.agents.empty')}
              </div>
            )}
          </div>

          <div className="mt-6 flex justify-end space-x-2">
            <Button
              variant="outline"
              onClick={onClose}
              className="bg-zinc-900 border-zinc-800 text-zinc-400 hover:bg-emerald-900/20 hover:border-emerald-500/30 hover:text-emerald-400 transition-colors duration-200"
            >
              {t('message_composition.form.typebot.buttons.cancel')}
            </Button>
            <Button
              onClick={handleSubmit}
              className="bg-emerald-600 hover:bg-emerald-700 transition-colors duration-200"
            >
              {t('message_composition.form.typebot.buttons.save')}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

// Exporte o componente com dynamic import e ssr desabilitado
export const DynamicAgentsConfig = dynamic(
  () => Promise.resolve(AgentsConfig),
  { 
    ssr: false,
  }
) 