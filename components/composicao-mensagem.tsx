import { NextResponse } from 'next/server'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { MessageSquare, Upload, Send, X, Bot, Clock, ChevronUp, Pencil, Users, Tag, Tags } from 'lucide-react'
import ProgressoDisparo from "./progresso-disparo"
import { uploadMedia } from "@/services/mediaService"
import type { Contact, Instance } from "@/types"
import { VariablesPopover } from "./variables-popover"
import { TypebotConfig } from "./typebot-config"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { DynamicAgentsConfig } from "./chatwoot-agents"
import { DynamicLabelsConfig } from "./chatwoot-labels"
import { useTranslation } from '@/hooks/useTranslation'

const MAX_CHARS = 65536

interface ComposicaoMensagemProps {
  selectedInstances: Instance[]
  contacts: Contact[]
}

interface Contact {
  id: number
  phone_number: string
}

interface Conversation {
  id: number
}

// Função para buscar contato
async function searchContact(phoneNumber: string): Promise<Contact | null> {
  try {
    const response = await fetch(`/api/chatwoot/contacts/search?q=${phoneNumber}`)
    const data = await response.json()
    
    if (data.payload && data.payload.length > 0) {
      return {
        id: data.payload[0].id,
        phone_number: data.payload[0].phone_number
      }
    }
    return null
  } catch (error) {
    console.error('Erro ao buscar contato:', error)
    return null
  }
}

// Função para buscar conversas do contato
async function getContactConversations(contactId: number): Promise<number | null> {
  try {
    const response = await fetch(`/api/chatwoot/contacts/${contactId}/conversations`)
    const data = await response.json()
    
    if (data.payload && data.payload.length > 0) {
      return data.payload[0].messages[0].conversation_id
    }
    return null
  } catch (error) {
    console.error('Erro ao buscar conversas:', error)
    return null
  }
}

// Função para atribuir conversa a um agente
async function assignConversation(conversationId: number, assigneeId: number): Promise<boolean> {
  try {
    const response = await fetch(`/api/chatwoot/conversations/${conversationId}/assignments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ assignee_id: assigneeId })
    })
    
    return response.ok
  } catch (error) {
    console.error('Erro ao atribuir conversa:', error)
    return false
  }
}

// Função para escolher um agente aleatoriamente
function getRandomAgent(agents: Agent[]): Agent | null {
  if (!agents.length) return null
  const randomIndex = Math.floor(Math.random() * agents.length)
  return agents[randomIndex]
}

// Modifique a função de envio de mensagem para incluir a atribuição
async function handleSendMessage() {
  try {
    // ... código existente de envio de mensagem ...

    // Após o envio bem-sucedido da mensagem
    if (selectedAgents.length > 0 && phoneNumber) { // phoneNumber deve vir do retorno da API da evolution
      // Busca o contato
      const contact = await searchContact(phoneNumber)
      
      if (contact) {
        // Busca a conversa
        const conversationId = await getContactConversations(contact.id)
        
        if (conversationId) {
          // Escolhe um agente aleatório
          const randomAgent = getRandomAgent(selectedAgents)
          
          if (randomAgent) {
            // Atribui a conversa ao agente escolhido
            await assignConversation(conversationId, randomAgent.id)
          }
        }
      }
    }

    // ... resto do código existente ...
  } catch (error) {
    console.error('Erro ao processar mensagem:', error)
  }
}

interface ChatwootLabel {
  title: string
  description: string
}

export function ComposicaoMensagemComponent({ selectedInstances, contacts }: ComposicaoMensagemProps) {
  const { t } = useTranslation()
  const [message, setMessage] = useState('')
  const [media, setMedia] = useState<{
    url: string;
    type: string;
    name?: string;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false)
  const [showProgress, setShowProgress] = useState(false)
  const [minTime, setMinTime] = useState('5')
  const [maxTime, setMaxTime] = useState('30')
  const charCount = message.length
  const [showVariables, setShowVariables] = useState(false)
  const [showTypebot, setShowTypebot] = useState(false)
  const [typebotActive, setTypebotActive] = useState(false)
  const [typebotConfig, setTypebotConfig] = useState({
    url: '',
    typebot: ''
  })
  const [variations, setVariations] = useState<string[]>([])
  const [showVariationsList, setShowVariationsList] = useState(false)
  const [selectedVariation, setSelectedVariation] = useState<number | null>(null)
  const [variables, setVariables] = useState<{ key: string; value: string }[]>([]);
  const [isTypebotConfigured, setIsTypebotConfigured] = useState(false);
  const [agents, setAgents] = useState<{ id: string; name: string }[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [showAgentsConfig, setShowAgentsConfig] = useState(false)
  const [selectedAgents, setSelectedAgents] = useState<Array<{ id: string; name: string }>>([])
  const [selectedLabels, setSelectedLabels] = useState<ChatwootLabel[]>([])
  const [showLabelsConfig, setShowLabelsConfig] = useState(false)
  const [labels, setLabels] = useState<ChatwootLabel[]>([])
  const [labelsError, setLabelsError] = useState<string | null>(null)

  // Novo estado para controlar se a integração está ativa
  const isChatwootEnabled = process.env.NEXT_PUBLIC_CHATWOOT_INTEGRATION === 'true'

  // Função para obter as variáveis disponíveis a partir dos contatos
  useEffect(() => {
    const availableVariables = contacts.map(contact => {
      const variables = {
        key: contact.phone,
        value: contact.name,
      };

      // Adiciona valores dinâmicos começando do índice 1
      for (let i = 1; i <= 5; i++) {
        const dynamicValue = contact[`value${i}`];
        if (dynamicValue) {
          variables[`value${i}`] = dynamicValue;
        }
      }

      return variables;
    });

    setVariables(availableVariables);
  }, [contacts]);

  const availableVariablesCount = contacts.length > 0 
    ? Object.entries(contacts[0])
        .filter(([key]) => key !== 'id' && ['name', 'phone', 'value1', 'value2', 'value3', 'value4', 'value5'].includes(key))
        .filter(([_, value]) => value)
        .length 
    : 0;

  const handleMessageChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value
    if (text.length <= MAX_CHARS) {
      setMessage(text)
    }
  }

  const handleMediaUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const allowedImageTypes = ['image/png', 'image/jpeg', 'image/jpg'];
      const allowedVideoTypes = ['video/mp4'];
      const allowedDocumentTypes = ['application/pdf'];

      let formattedName = '';

      try {
        if (allowedImageTypes.includes(file.type)) {
          formattedName = 'imagem.png';
          const result = await uploadMedia(file, formattedName);
          console.log('URL do arquivo:', `${process.env.NEXT_PUBLIC_APP_URL}${result.url}`);
          setMedia({
            url: `${process.env.NEXT_PUBLIC_APP_URL}${result.url}`,
            type: file.type,
            name: formattedName
          });
        } else if (allowedVideoTypes.includes(file.type)) {
          formattedName = 'video.mp4';
          const result = await uploadMedia(file, formattedName);
          console.log('URL do arquivo:', `${process.env.NEXT_PUBLIC_APP_URL}${result.url}`);
          setMedia({
            url: `${process.env.NEXT_PUBLIC_APP_URL}${result.url}`,
            type: file.type,
            name: formattedName
          });
        } else if (allowedDocumentTypes.includes(file.type)) {
          formattedName = 'arquivo.pdf';
          const result = await uploadMedia(file, formattedName);
          console.log('URL do arquivo:', `${process.env.NEXT_PUBLIC_APP_URL}${result.url}`);
          setMedia({
            url: `${process.env.NEXT_PUBLIC_APP_URL}${result.url}`,
            type: file.type,
            name: formattedName
          });
        } else {
          alert('Formato de arquivo não suportado. Apenas PNG, JPG, JPEG, MP4 e PDF são permitidos.');
        }
      } catch (error) {
        console.error('Erro no upload:', error);
        alert('Erro ao fazer upload do arquivo');
      }
    }
  };

  const handleVariableSelect = (variable: string) => {
    const textarea = document.getElementById('message') as HTMLTextAreaElement
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const newMessage = message.substring(0, start) + variable + message.substring(end)
    setMessage(newMessage)
    
    // Reposiciona o cursor após a variável inserida
    setTimeout(() => {
      textarea.focus()
      const newCursorPos = start + variable.length
      textarea.setSelectionRange(newCursorPos, newCursorPos)
    }, 0)
  }

  const handleSubmit = async () => {
    if (!message.trim() && variations.length === 0) return;

    // Criar array com todas as variações existentes
    const allMessages = [...variations];
    
    // Se houver texto no campo e não for duplicado, adiciona ao array
    if (message.trim() && !variations.includes(message)) {
      allMessages.push(message);
    }

    // Ao invés de retornar o componente, atualiza o estado para mostrar o progresso
    setShowProgress(true);
  }

  const handleTypebotSubmit = (config: { url: string; typebot: string }) => {
    try {
      new URL(config.url);
      setTypebotConfig(config);
      setIsTypebotConfigured(true);
      setShowTypebot(false);
    } catch (error) {
      alert(t('message_composition.errors.invalid_url'));
      return;
    }
  };

  useEffect(() => {
    if (selectedVariation !== null) {
        const newVariations = [...variations];
        newVariations[selectedVariation] = message; // Atualiza o template selecionado
        setVariations(newVariations);
    }
  }, [message]); // Executa sempre que a mensagem mudar

  const handleAddOrUpdateVariation = () => {
    if (message.trim()) {
        if (variations.length >= 3) {
            alert(t('message_composition.errors.template_limit'));
            return;
        }
        if (selectedVariation !== null) {
            // Atualiza o template selecionado
            const newVariations = [...variations];
            newVariations[selectedVariation] = message;
            setVariations(newVariations);
        } else {
            // Adiciona um novo template
            const newVariations = [...variations, message];
            setVariations(newVariations);
            
            // Seleciona automaticamente o terceiro template se houver 3 templates
            if (newVariations.length === 3) {
                setSelectedVariation(2); // Seleciona o terceiro template (índice 2)
            } else {
                // Limpa o campo de texto se não houver 3 templates
                setMessage(''); // Limpa o campo de texto
            }
        }
    }
  }

  const handleViewVariation = (text: string) => {
    setMessage(text)
  }

  const handleRemoveVariation = (index: number) => {
    const newVariations = variations.filter((_, i) => i !== index)
    setVariations(newVariations)
  }

  useEffect(() => {
    console.clear();
    console.log(`
      ============================================================
                        📋 CONTATOS IMPORTADOS 📋
      ============================================================

      Total de Contatos: ${contacts.length}
      Total de Variáveis por Contato: ${Object.keys(contacts[0] || {}).length}

      ------------------------------------------------------------

      Variáveis Disponíveis:
      ${contacts[0] ? Object.keys(contacts[0]).map((key, index) => `
       ${index + 1}. ${key}`).join('')
      : 'Nenhuma variável disponível'}
      
      ============================================================
    `);
  }, []);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const response = await fetch('/api/chatwoot/agents')
        
        if (!response.ok) {
          console.error('Erro ao buscar agentes:', response.statusText)
          return
        }

        const data = await response.json()
        setAgents(Array.isArray(data) ? data : data.payload || [])
      } catch (error) {
        console.error('Erro ao buscar agentes:', error)
      }
    }

    // Só executa se a integração estiver ativada
    if (isChatwootEnabled) {
      fetchAgents()
    }
  }, [isChatwootEnabled]) // Adiciona isChatwootEnabled como dependência

  const handleAgentsSubmit = (agents: Array<{ id: string; name: string }>) => {
    setSelectedAgents(agents)
    setShowAgentsConfig(false)
  }

  // Função para buscar as labels
  useEffect(() => {
    const fetchLabels = async () => {
      try {
        console.log('🏷️ Iniciando busca de labels...')
        const response = await fetch('/api/chatwoot/labels')
        
        if (!response.ok) {
          throw new Error(`Erro HTTP: ${response.status} - ${response.statusText}`)
        }

        const data = await response.json()
        console.log('📦 Resposta da API de labels:', data)

        if (!data || (!Array.isArray(data) && !data.payload)) {
          throw new Error('Formato de resposta inválido')
        }

        const labelsData = Array.isArray(data) ? data : data.payload
        setLabels(labelsData)
        console.log('✅ Labels carregadas com sucesso:', labelsData)
        setLabelsError(null)
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido'
        console.error('❌ Erro ao buscar labels:', {
          message: errorMessage,
          error
        })
        setLabelsError(`Erro ao carregar labels: ${errorMessage}`)
        setLabels([])
      }
    }

    if (isChatwootEnabled) {
      fetchLabels()
    }
  }, [isChatwootEnabled])

  if (showProgress) {
    const allMessages = [...variations];
    if (message.trim() && !variations.includes(message)) {
      allMessages.push(message);
    }
    return <ProgressoDisparo 
      selectedInstances={selectedInstances}
      contacts={contacts}
      mediaInfo={media}
      isTypebotConfigured={isTypebotConfigured}
      typebotConfig={typebotConfig}
      minTime={parseInt(minTime)}
      maxTime={parseInt(maxTime)}
      message={allMessages.length > 0 ? allMessages : message}
      selectedAgents={selectedAgents}
      selectedLabels={selectedLabels}
    />
  }

  return (
    <div className="flex flex-col min-h-screen bg-black">
      <div className="flex-grow flex items-center justify-center p-4">
        <Card className="w-full max-w-xl bg-zinc-950 border-zinc-900 shadow-2xl">
          <CardHeader className="border-b border-zinc-900 pb-4">
            <CardTitle className="text-2xl font-bold text-center text-zinc-100 flex items-center justify-center">
              <MessageSquare className="mr-2 text-emerald-500 h-5 w-5" />
              {t('message_composition.title')}
            </CardTitle>
            <p className="text-zinc-400 text-center mt-1 text-sm">
              {t('message_composition.subtitle')}
            </p>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="space-y-4">
              <div className="relative">
                <div className="flex justify-between items-center mb-2">
                  <Label htmlFor="message" className="text-zinc-300">
                    {t('message_composition.form.message')}
                  </Label>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className={`text-zinc-400 bg-zinc-900 border-zinc-800 transition duration-200 ${
                        showVariables ? 'bg-zinc-800 text-white' : 'hover:bg-zinc-700 hover:text-emerald-400'
                      }`}
                      onClick={() => setShowVariables(!showVariables)}
                    >
                      {t('message_composition.form.available_variables').replace('{count}', availableVariablesCount.toString())}
                      <span className={`ml-2 transform transition-transform ${showVariables ? '' : 'rotate-180'}`}>
                        <ChevronUp className="h-4 w-4" />
                      </span>
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-zinc-400 hover:bg-zinc-800 hover:text-emerald-400 bg-zinc-900 border-zinc-800 transition duration-200"
                      onClick={handleAddOrUpdateVariation}
                      disabled={!message.trim() || variations.length >= 3}
                    >
                      {t('message_composition.form.add_template')}
                    </Button>
                  </div>
                </div>
                
                {showVariables && (
                  <div className="relative mb-2">
                    <VariablesPopover 
                      onSelectVariable={handleVariableSelect} 
                      contacts={contacts} 
                    />
                  </div>
                )}
                
                <Textarea
                  id="message"
                  placeholder={t('message_composition.form.message_placeholder')}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="mt-1 w-full h-52 bg-zinc-900 border-zinc-800 text-zinc-100 resize-none pr-20 pb-8"
                  maxLength={MAX_CHARS}
                />
                <div className="absolute bottom-2 right-2 text-zinc-400 text-sm bg-zinc-900 px-2 py-1 rounded">
                  {charCount} / {MAX_CHARS}
                </div>
              </div>

              {variations.length > 0 && (
                <div className="grid grid-cols-3 gap-2">
                  {variations.map((variation, index) => (
                    <div
                      key={index}
                      className={`flex items-center justify-between px-3 py-1.5 rounded-md cursor-pointer ${
                        selectedVariation === index
                          ? 'bg-emerald-900/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-zinc-900 text-zinc-400 border border-zinc-800 hover:border-zinc-700'
                      }`}
                      onClick={() => {
                        if (selectedVariation === index) {
                          setSelectedVariation(null)
                        } else {
                          setMessage(variation)
                          setSelectedVariation(index)
                        }
                      }}
                    >
                      <span className="text-sm"> {`${t('message_composition.form.template_label')} | #${(index + 1).toString().padStart(2, '0')}`}</span>
                      <div className="flex items-center gap-1 ml-2 border-l border-zinc-800 pl-2">
                        <Pencil 
                          className="h-3 w-3 hover:text-zinc-300 cursor-pointer" 
                          onClick={(e) => {
                            e.stopPropagation()
                            setMessage(variation)
                            setSelectedVariation(index)
                          }}
                        />
                        <X
                          className="h-3 w-3 text-red-400 hover:text-red-300 cursor-pointer"
                          onClick={(e) => {
                            e.stopPropagation()
                            const newVariations = variations.filter((_, i) => i !== index)
                            setVariations(newVariations)
                            if (selectedVariation === index) {
                              setSelectedVariation(null)
                              setMessage('')
                            }
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="space-y-4">
                {/* Primeira linha: Arquivo e Typebot */}
                <div className="flex gap-4">
                  <div className="w-1/2">
                    <Label className="text-zinc-300">
                      {t('message_composition.form.media.title')}
                    </Label>
                    <div className="flex items-center mt-1">
                      <Button
                        variant="outline"
                        onClick={() => document.getElementById('media-upload')?.click()}
                        className={`w-full gap-2 transition-colors duration-200
                          ${media
                            ? 'bg-emerald-900/20 border-emerald-500/30 text-emerald-400 hover:bg-emerald-900/30'
                            : 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-emerald-900/20 hover:border-emerald-500/30 hover:text-emerald-400'
                          }`}
                      >
                        <Upload className="h-4 w-4" />
                        {media ? media.name : t('message_composition.form.media.select_file')}
                      </Button>
                      <input
                        id="media-upload"
                        type="file"
                        accept="image/*,video/*"
                        onChange={handleMediaUpload}
                        className="hidden"
                      />
                    </div>
                  </div>

                  <div className="w-1/2">
                    <Label className="text-zinc-300">
                      {t('message_composition.form.typebot.title')}
                    </Label>
                    <div className="flex items-center mt-1">
                      <Button
                        variant="outline"
                        onClick={isTypebotConfigured ? undefined : () => setShowTypebot(true)}
                        className={`w-full gap-2 transition-colors duration-200
                          ${isTypebotConfigured
                            ? 'bg-emerald-900/20 border-emerald-500/30 text-emerald-400 hover:bg-emerald-900/30'
                            : 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-emerald-900/20 hover:border-emerald-500/30 hover:text-emerald-400'
                          }`}
                      >
                        <Bot className="h-4 w-4" />
                        {isTypebotConfigured 
                          ? t('message_composition.form.typebot.added') 
                          : t('message.typebot.button')}
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Segunda linha: Agentes e Marcadores */}
                {isChatwootEnabled && (
                  <div className="flex gap-4">
                    <div className="w-1/2">
                      <Label className="text-zinc-300">
                        {t('message_composition.form.agents.title')}
                      </Label>
                      <div className="flex items-center mt-1">
                        <Button
                          variant="outline"
                          onClick={() => setShowAgentsConfig(true)}
                          className={`w-full gap-2 transition-colors duration-200
                            ${selectedAgents.length > 0
                              ? 'bg-emerald-900/20 border-emerald-500/30 text-emerald-300 hover:bg-emerald-900/30 hover:text-emerald-200'
                              : 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-emerald-900/20 hover:border-emerald-500/30 hover:text-emerald-400'
                            }`}
                        >
                          <Users className="h-4 w-4" />
                          {selectedAgents.length > 0 
                            ? `${selectedAgents.length} ${t('message_composition.form.agents.selected')}`
                            : t('message_composition.form.agents.button')}
                        </Button>
                      </div>
                    </div>

                    <div className="w-1/2">
                      <Label className="text-zinc-300">
                        {t('message_composition.form.labels.title')}
                      </Label>
                      <div className="flex items-center mt-1">
                        <Button
                          variant="outline"
                          onClick={() => setShowLabelsConfig(true)}
                          className={`w-full gap-2 transition-colors duration-200
                            ${selectedLabels.length > 0
                              ? 'bg-emerald-900/20 border-emerald-500/30 text-emerald-300 hover:bg-emerald-900/30 hover:text-emerald-200'
                              : 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-emerald-900/20 hover:border-emerald-500/30 hover:text-emerald-400'
                            }`}
                        >
                          <Tags className="h-4 w-4" />
                          {selectedLabels.length > 0
                            ? `${selectedLabels.length} ${t('message_composition.form.labels.selected')}`
                            : t('message_composition.form.labels.button')}
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Terceira linha: Tempos */}
                <div className="flex gap-4">
                  <div className="w-1/2">
                    <Label htmlFor="min-time" className="text-zinc-300">
                      {t('message_composition.form.timing.min_time')}
                    </Label>
                    <div className="relative mt-1">
                      <Input
                        id="min-time"
                        type="number"
                        min="1"
                        value={minTime}
                        onChange={(e) => setMinTime(e.target.value)}
                        className="w-full bg-zinc-900 border-zinc-800 text-zinc-100 pl-9"
                      />
                      <Clock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
                    </div>
                  </div>

                  <div className="w-1/2">
                    <Label htmlFor="max-time" className="text-zinc-300">
                      {t('message_composition.form.timing.max_time')}
                    </Label>
                    <div className="relative mt-1">
                      <Input
                        id="max-time"
                        type="number"
                        min="1"
                        value={maxTime}
                        onChange={(e) => setMaxTime(e.target.value)}
                        className="w-full bg-zinc-900 border-zinc-800 text-zinc-100 pl-9"
                      />
                      <Clock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col items-center border-t border-zinc-900 pt-4">
            <Button 
              onClick={handleSubmit} 
              className="w-full bg-emerald-600 hover:bg-emerald-700"
              disabled={!message.trim() || isLoading}
            >
              <Send className="mr-2 h-4 w-4" />
              {t('message_composition.buttons.send')}
            </Button>
          </CardFooter>
        </Card>
      </div>
      {showTypebot && (
        <TypebotConfig
          onSubmit={handleTypebotSubmit}
          onClose={() => setShowTypebot(false)}
        />
      )}
      {showAgentsConfig && isChatwootEnabled && (
        <DynamicAgentsConfig
          agents={agents}
          selectedAgents={selectedAgents}
          onSubmit={handleAgentsSubmit}
          onClose={() => setShowAgentsConfig(false)}
        />
      )}
      {showLabelsConfig && (
        <DynamicLabelsConfig
          labels={labels}
          selectedLabels={selectedLabels}
          onSubmit={(labels) => {
            setSelectedLabels(labels)
            setShowLabelsConfig(false)
          }}
          onClose={() => setShowLabelsConfig(false)}
        />
      )}
      {labelsError && (
        <div className="text-red-400 text-sm mt-1">
          {labelsError}
        </div>
      )}
    </div>
  )
}