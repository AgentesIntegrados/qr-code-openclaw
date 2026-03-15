'use client'

import { useEffect, useState } from "react"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ChevronRight, Server, CheckCircle, Loader2, Search } from 'lucide-react'
import { fetchInstances } from '@/utils/fetchInstances'
import type { Instance } from "@/types"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { useTranslation } from '@/hooks/useTranslation'

interface SelecaoInstanciasProps {
  onNextStep: (instances: Instance[]) => void
}

export function SelecaoInstanciasComponent({ onNextStep }: SelecaoInstanciasProps) {
  const { t } = useTranslation()
  const [instances, setInstances] = useState<Instance[]>([])
  const [selectedInstances, setSelectedInstances] = useState<Instance[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [activeFilter, setActiveFilter] = useState<'all' | 'baileys' | 'business'>('all')
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectAll, setSelectAll] = useState(false);

  useEffect(() => {
    const loadInstances = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const fetchedInstances = await fetchInstances()
        setInstances(fetchedInstances)
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Erro desconhecido')
      } finally {
        setIsLoading(false)
      }
    }

    loadInstances()
  }, [])

  const handleInstanceToggle = (instance: Instance) => {
    setSelectedInstances(prev =>
      prev.some(i => i.id === instance.id)
        ? prev.filter(i => i.id !== instance.id)
        : [...prev, instance]
    )
  }

  const handleNextStep = () => {
    onNextStep(selectedInstances)
  }

  const filteredInstances = instances.filter(instance =>
    instance.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const openModal = () => {
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-black p-6">
        <Card className="bg-red-950/20 border-red-900 w-full max-w-xl">
          <CardContent className="pt-6">
            <div className="text-center text-red-500">
              {error}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-screen bg-black">
      <div className="flex-grow flex items-center justify-center p-4">
        <Card className="w-full max-w-xl bg-zinc-950 border-zinc-900 shadow-2xl">
          <CardHeader className="border-b border-zinc-900 pb-4">
            <CardTitle className="text-2xl font-bold text-center text-zinc-100 flex items-center justify-center">
              <Server className="mr-2 text-emerald-500 h-5 w-5" />
              {t('instances.title')}
            </CardTitle>
            <p className="text-zinc-400 text-center mt-1 text-sm">
              {t('instances.subtitle')}
            </p>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-zinc-400" />
              <Input
                type="text"
                placeholder={t('instances.search_placeholder')}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-zinc-900 border-zinc-800 text-zinc-100 pl-10 pr-2 w-full"
              />
            </div>
            <ScrollArea className="h-[400px] pr-0 overflow-y-auto">
              <div className="space-y-2">
                {filteredInstances.map((instance) => (
                  <Card 
                    key={instance.id} 
                    className={`bg-zinc-900 border transition-all duration-300 ease-in-out cursor-pointer ${
                      selectedInstances.some(i => i.id === instance.id)
                        ? 'border-emerald-500 shadow-emerald-500/20 shadow-sm' 
                        : 'border-zinc-800 hover:border-zinc-700'
                    } w-full`}
                    onClick={() => handleInstanceToggle(instance)}
                  >
                    <CardContent className="p-3 flex items-center space-x-3">
                      <div className="flex items-center space-x-3 w-full">
                        <Checkbox
                          checked={selectedInstances.some(i => i.id === instance.id)}
                          onCheckedChange={() => handleInstanceToggle(instance)}
                          onClick={(e) => e.stopPropagation()}
                          className="border-zinc-700 data-[state=checked]:bg-emerald-500 data-[state=checked]:border-emerald-500"
                        />
                        <div className="flex-grow">
                          <div className="flex items-center gap-2">
                            <div className="text-base font-medium text-zinc-100 hover:text-emerald-400 transition-colors">
                              {instance.name}
                            </div>
                            <Badge 
                              variant="default"
                              className="bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 flex items-center gap-1"
                            >
                              {instance.integration === 'WHATSAPP-BAILEYS' ? 'Baileys' : 'Business'}
                            </Badge>
                          </div>
                          <p className="text-xs text-zinc-500 mt-0.5">{instance.ownerJid}</p>
                        </div>
                        {selectedInstances.some(i => i.id === instance.id) && (
                          <CheckCircle className="h-5 w-5 text-emerald-500 flex-shrink-0" />
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
          <CardFooter className="flex flex-col items-center border-t border-zinc-900 pt-4 mt-2">
            <span 
              className="text-center text-sm text-emerald-500 mb-1 cursor-pointer hover:underline hover:text-emerald-400" 
              onClick={() => {
                if (selectAll) {
                  setSelectedInstances([]);
                } else {
                  setSelectedInstances(filteredInstances);
                }
                setSelectAll(!selectAll);
              }}
            >
              {selectedInstances.length === filteredInstances.length ? t('instances.selection.deselect_all') : t('instances.selection.select_all')}
            </span>
            <p className="text-zinc-400 mb-3 text-sm">
              {t('instances.selection.count').replace('{selected}', selectedInstances.length.toString()).replace('{total}', searchTerm ? filteredInstances.length.toString() : instances.length.toString())}
            </p>
            <Button 
              onClick={handleNextStep} 
              className="w-full max-w-md bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 rounded-full transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              disabled={selectedInstances.length === 0}
            >
              {t('instances.buttons.next')}
              <ChevronRight className="ml-2 h-4 w-4" />
            </Button>
          </CardFooter>
        </Card>
      </div>
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50" onClick={closeModal}>
          <div className="relative z-60">
            {/* Conteúdo do modal */}
          </div>
        </div>
      )}
    </div>
  )
}