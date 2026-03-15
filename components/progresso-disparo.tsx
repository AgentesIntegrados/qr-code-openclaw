'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { saveAs } from 'file-saver'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { CheckCircle, XCircle, AlertCircle, RefreshCw, MessageCircle, StopCircle, Clock, Download as DownloadIcon } from 'lucide-react'
import Header from '@/components/header'
import { sendMessage } from '../services/messageService';
import { sendMediaMessage } from '../services/sendMedia';
import { startTypebot } from '../services/typebotService';
import { useTranslation } from '@/hooks/useTranslation'

interface StatusInfo {
  pendentes: number;
  enviadas: number;
  erros: number;
  total: number;
}

interface ContatoReport {
  numero: string;
  status: 'Sucesso' | 'Erro' | 'Cancelado';
  instancia: string;
  templateNumero: string;
  mensagem: string;
  enviadoEm: string;
  agente?: string;
  labels?: string;
}

interface ChatwootLabel {
  title: string;
  description: string;
}

interface ProgressoDisparoProps {
  selectedInstances: string[];
  contacts: Contact[];
  message: string | string[];
  minTime: number;
  maxTime: number;
  mediaInfo?: {
    url: string;
    type: string;
    name: string;
  } | null;
  isTypebotConfigured: boolean;
  typebotConfig: {
    url: string;
    typebot: string;
  };
  selectedAgents?: any[];
  selectedLabels?: ChatwootLabel[];
}

export default function ProgressoDisparo({
  selectedInstances,
  contacts,
  message,
  minTime,
  maxTime,
  mediaInfo,
  isTypebotConfigured,
  typebotConfig,
  selectedAgents,
  selectedLabels
}: ProgressoDisparoProps) {
  const { t } = useTranslation()
  const baseUrl = process.env.NEXT_PUBLIC_EVOLUTION_URL
  const apikey = process.env.NEXT_PUBLIC_EVOLUTION_API

  const [status, setStatus] = useState<StatusInfo>({
    pendentes: contacts.length,
    enviadas: 0,
    erros: 0,
    total: contacts.length
  })
  const [isComplete, setIsComplete] = useState(false)
  const [currentAction, setCurrentAction] = useState<string>('')
  const [isCancelled, setIsCancelled] = useState(false)
  const [contatosData, setContatosData] = useState<{ contato: string; status: 'sucesso' | 'erro' }[]>([])
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const isExecuting = useRef(false);
  const userCancelled = useRef(false);
  const isSending = useRef(false);
  const processedContacts = useRef<Set<string>>(new Set());

  const handleError = useCallback((error: Error, contact: Contact) => {
    console.error(`❌ Erro ao enviar para ${contact.number}:`, error);
    setStatus(prev => ({
      ...prev,
      erros: prev.erros + 1,
      pendentes: prev.pendentes - 1
    }));
    setContatosData(prev => [...prev, {
      contato: contact.phone,
      status: 'erro'
    }]);
  }, []);

  const processMessageVariables = (message: string, variables: Record<string, string>) => {
    let processedMessage = message;
    
    // Mapeamento das chaves para os formatos esperados
    const keyMap: { [key: string]: string } = {
      numero: 'phone',
      nome: 'name',
      valor1: 'value1',
      valor2: 'value2',
      valor3: 'value3',
      valor4: 'value4',
      valor5: 'value5'
    };
    
    // Substitui variáveis no formato [nome]
    Object.entries(keyMap).forEach(([ptKey, enKey]) => {
      const bracketRegex = new RegExp(`\\[${ptKey}\\]`, 'g');
      if (variables[enKey]) {
        processedMessage = processedMessage.replace(bracketRegex, variables[enKey]);
      }
    });
    
    // Substitui variáveis no formato {{nome}}
    Object.entries(keyMap).forEach(([ptKey, enKey]) => {
      const curlyRegex = new RegExp(`{{${ptKey}}}`, 'g');
      if (variables[enKey]) {
        processedMessage = processedMessage.replace(curlyRegex, variables[enKey]);
      }
    });
    
    return processedMessage;
  };

  const sendMessageToContact = useCallback(async (contact: Contact, instance: string) => {
    const { phone, id, ...variables } = contact;
    let success = false;
    let attempts = 0;

    const selectedMessage = Array.isArray(message) 
      ? message[Math.floor(Math.random() * message.length)]
      : message;

    const templateIndex = Array.isArray(message) 
      ? message.indexOf(selectedMessage) + 1
      : 1;

    const instanceName = typeof instance === 'object' ? instance.name || instance.toString() : instance;
    
    // Processa a mensagem com as variáveis
    const processedMessage = processMessageVariables(selectedMessage, {
      phone: contact.phone,
      name: contact.name || '',
      value1: contact.value1 || '',
      value2: contact.value2 || '',
      value3: contact.value3 || '',
      value4: contact.value4 || '',
      value5: contact.value5 || ''
    });

    while (attempts < 4 && !success && !isCancelled) {
      if (attempts === 0) {
        console.log(`📱 Iniciando envio para ${phone} usando instância ${instanceName}`);
        setCurrentAction(`${t('progress.status.sending')
          .replace('{phone}', phone)}`)
      } else {
        console.log(`⚠️ Tentativa ${attempts + 1}/3 para ${phone} usando instância ${instanceName}`);
        setCurrentAction(`${t('progress.status.retry')
          .replace('{attempt}', (attempts + 1).toString())
          .replace('{phone}', phone)}`)
      }
      
      try {
        if (mediaInfo) {
          // Envio de mídia usando o novo componente
          await sendMediaMessage(phone, {
            ...mediaInfo,
            name: mediaInfo.url.split('/').pop() || 'arquivo'
          }, processedMessage, instanceName, apikey!, baseUrl!);
          console.log(`✅ Mídia enviada com sucesso para ${phone} na tentativa ${attempts + 1} (instância: ${instanceName})`);
          setCurrentAction(`${t('progress.status.media_success')
            .replace('{phone}', phone)}`)
          setStatus(prevStatus => ({
            ...prevStatus,
            enviadas: prevStatus.enviadas + 1,
            pendentes: prevStatus.pendentes - 1
          }));
          success = true;
          break;
        } else {
          // Envio de mensagem de texto
          const response = await sendMessage(phone, processedMessage, instanceName, variables);
          console.log('📨 Resposta da Evolution:', response);

          if (response.ok) {
            console.log(`✅ Mensagem enviada com sucesso para ${phone} na tentativa ${attempts + 1} (instância: ${instanceName})`);
            setCurrentAction(`${t('progress.status.message_success')
              .replace('{phone}', phone)}`)

            // Adiciona o registro inicial de sucesso
            setContatosData(prev => [...prev, {
              numero: phone,
              status: 'Sucesso',
              instancia: instanceName,
              templateNumero: `Template ${templateIndex}`,
              mensagem: processedMessage,
              enviadoEm: new Date().toLocaleTimeString(),
              agente: selectedAgents?.length > 0 ? 'Pendente atribuição' : '-',
              labels: selectedLabels?.length > 0 ? 'Pendente atribuição' : '-'
            }]);

            try {
              // Verifica se existem agentes selecionados antes de prosseguir com a lógica do Chatwoot
              if (selectedAgents?.length > 0 || selectedLabels?.length > 0) {
                console.log('\n🤖 Iniciando processo no Chatwoot...')
                
                try {
                  const numeroFormatado = formatarNumeroChatwoot(phone)
                  console.log('\n🔄 Formatação do número para busca:')
                  console.log(`• Número original: ${phone}`)
                  console.log(`• Número formatado: ${numeroFormatado}`)
                  // Aumenta o delay para 3 segundos antes de buscar a conversa
                  console.log('⏳ Sincronizando com o chatwoot...')
                  await new Promise(resolve => setTimeout(resolve, 4000))
                  
                  const contatoResponse = await fetch(`/api/chatwoot/contacts/search?q=${numeroFormatado}`)
                  const contatoData = await contatoResponse.json()
                  
                  if (contatoData.payload?.length > 0) {
                    const contatoId = contatoData.payload[0].id
                    console.log(`✅ Contato encontrado no Chatwoot. ID: ${contatoId}`)

                    await new Promise(resolve => setTimeout(resolve, 4000))
                    
                    const conversasResponse = await fetch(`/api/chatwoot/contacts/${contatoId}/conversations`)
                    const conversasData = await conversasResponse.json()
                    
                    if (conversasData.payload?.length > 0) {
                      const conversationId = conversasData.payload[0].messages[0].conversation_id
                      console.log(`✅ Conversa encontrada. ID: ${conversationId}`)
                      
                      // Atribuição do agente
                      if (selectedAgents?.length > 0) {
                        const randomIndex = Math.floor(Math.random() * selectedAgents.length)
                        const randomAgent = selectedAgents[randomIndex]
                        
                        console.log('\n👥 Seleção do agente:')
                        console.log(`• Total de agentes disponíveis: ${selectedAgents.length}`)
                        console.log(`• Índice sorteado: ${randomIndex}`)
                        console.log(`• Agente selecionado: ${randomAgent.name} (ID: ${randomAgent.id})`)
                        
                        setCurrentAction(`${t('progress.status.chatwoot_agent')
                          .replace('{name}', randomAgent.name)}`)
                        
                        const atribuicaoResponse = await fetch(`/api/chatwoot/conversations/${conversationId}/assignments`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ assignee_id: randomAgent.id })
                        })
                        
                        if (atribuicaoResponse.ok) {
                          console.log(`✅ Conversa atribuída com sucesso ao agente ${randomAgent.name}`)
                          setContatosData(prev => [...prev, {
                            numero: phone,
                            status: 'Sucesso',
                            instancia: instanceName,
                            templateNumero: `Template ${templateIndex}`,
                            mensagem: processedMessage,
                            enviadoEm: new Date().toLocaleTimeString(),
                            agente: randomAgent.name
                          }])
                        } else {
                          console.error('❌ Erro ao atribuir agente:', await atribuicaoResponse.text())
                        }
                      }
                      
                      // Atribuição das labels
                      if (selectedLabels?.length > 0) {
                        console.log('\n🏷️ Atribuição de marcadores:')
                        console.log('• Marcadores selecionados:')
                        selectedLabels.forEach((label, index) => {
                          console.log(`  ${index + 1}. ${label.description} (${label.title})`)
                        })
                        
                        setCurrentAction(`${t('progress.status.chatwoot_labels')
                          .replace('{count}', selectedLabels.length.toString())
                          .replace('{plural}', selectedLabels.length === 1 ? '' : 'es')}`)
                        
                        const labelsResponse = await fetch(`/api/chatwoot/conversations/${conversationId}/labels`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            labels: selectedLabels.map(l => l.title)
                          })
                        })
                        
                        if (labelsResponse.ok) {
                          console.log('✅ Marcadores atribuídos com sucesso:')
                          selectedLabels.forEach((label, index) => {
                            console.log(`  ✓ ${label.description}`)
                          })
                          
                          // Atualiza o registro com as labels atribuídas
                          setContatosData(prev => {
                            const lastIndex = prev.length - 1
                            const updatedData = [...prev]
                            updatedData[lastIndex] = {
                              ...updatedData[lastIndex],
                              labels: selectedLabels.map(l => l.description).join(', ')
                            }
                            return updatedData
                          })
                        } else {
                          console.error('❌ Erro ao atribuir marcadores:', await labelsResponse.text())
                        }
                      }
                      
                      setCurrentAction(t('progress.status.chatwoot_complete'))
                    } else {
                      console.error('❌ Nenhuma conversa encontrada para o contato')
                    }
                  } else {
                    console.error('❌ Contato não encontrado no Chatwoot')
                  }
                } catch (error) {
                  console.error('❌ Erro no processo Chatwoot:', error)
                }
              } else {
                console.log('\n⏭️ Nenhum agente selecionado, continuando sem atribui��ão no Chatwoot')
              }
            } catch (error) {
              console.error('❌ Erro no processo de atribuição:', error)
            }

            setStatus(prevStatus => ({
              ...prevStatus,
              enviadas: prevStatus.enviadas + 1,
              pendentes: prevStatus.pendentes - 1
            }))
            success = true

            // Chama a função para iniciar o Typebot
            if (isTypebotConfigured) {
              await startTypebot(instanceName, typebotConfig.url, typebotConfig.typebot, phone, variables)
              console.log(`🤖 Typebot iniciado para ${phone}`)
            }

            break
          }
        }
      } catch (error) {
        console.error(`❌ Falha na tentativa ${attempts + 1}/3 para ${phone} (instância: ${instanceName}):`, error)
        
        if (attempts === 3) {
          console.log(`❌ Todas as tentativas falharam para ${phone} (instância: ${instanceName})`)
          setCurrentAction(t('progress.status.error'))
          setStatus(prevStatus => ({
            ...prevStatus,
            erros: prevStatus.erros + 1,
            pendentes: prevStatus.pendentes - 1
          }))
          setContatosData(prev => [...prev, {
            numero: phone,
            status: 'Erro',
            instancia: instanceName,
            templateNumero: `Template ${templateIndex}`,
            mensagem: processedMessage,
            enviadoEm: new Date().toLocaleTimeString()
          }])
        } else {
          console.log(`⏱️ Aguardando 2.5 segundos antes da próxima tentativa para ${phone}`)
          await new Promise(resolve => setTimeout(resolve, 2500))
        }
      }
      
      attempts++
    }

    return success
  }, [message, isCancelled, mediaInfo, handleError, selectedAgents, selectedLabels])

  const formatMessage = (template: string, variables: Record<string, any>) => {
    return template.replace(/\{(\w+)\}/g, (match, key) => {
      return variables[key]?.toString() || match
    })
  }

  const processNextContact = useCallback(async () => {
    if (isCancelled || userCancelled.current) {
      setIsComplete(true)
      setCurrentAction(t('progress.status.canceled'))
      return
    }

    const pendingContacts = contacts.filter(c => !processedContacts.current.has(c.id))
      .slice(0, selectedInstances.length)
    
    if (pendingContacts.length === 0) {
      setIsComplete(true)
      setCurrentAction(t('progress.status.completed'))
      return
    }

    try {
      const phoneNumbers = pendingContacts.map(c => c.phone).join(' e ')
      setCurrentAction(`${t('progress.status.sending')
        .replace('{phone}', phoneNumbers)}`)
      
      console.log(`
⚙️ PROCESSANDO LOTE DE ${pendingContacts.length} CONTATOS:
${pendingContacts.map((c, i) => {
  const instance = selectedInstances[i]
  const instanceName = typeof instance === 'object' ? instance.name : instance
  return `${i + 1}. ${c.phone} (instância: ${instanceName})`
}).join('\n')}
      `)

      const sendPromises = pendingContacts.map((contact, index) => {
        const instance = selectedInstances[index]
        return sendMessageToContact(contact, instance)
      })

      await Promise.all(sendPromises)

      pendingContacts.forEach(contact => processedContacts.current.add(contact.id))

      if (processedContacts.current.size < contacts.length) {
        const waitTime = (Math.floor(Math.random() * (maxTime - minTime + 1)) + minTime) * 1000
        const waitTimeSeconds = waitTime/1000
        
        console.log(`
⏱️ AGUARDANDO ${waitTimeSeconds} SEGUNDOS ANTES DO PRÓXIMO LOTE
• Contatos processados: ${processedContacts.current.size}/${contacts.length}
• Próximo lote em: ${new Date(Date.now() + waitTime).toLocaleTimeString()}
        `)
        
        setCurrentAction(`${t('progress.status.waiting')
          .replace('{seconds}', waitTimeSeconds.toString())}`)
        await new Promise(resolve => setTimeout(resolve, waitTime))
        await processNextContact()
      } else {
        setIsComplete(true)
        setCurrentAction(t('progress.status.completed'))
      }
    } catch (error) {
      console.error('❌ Erro ao processar lote de contatos:', error)
      pendingContacts.forEach(contact => {
        handleError(error as Error, contact)
        processedContacts.current.add(contact.id)
      })
    }
  }, [contacts, isCancelled, minTime, maxTime, selectedInstances, sendMessageToContact, handleError])

  useEffect(() => {
    const startDisparo = async () => {
      try {
        if (!isSending.current && !userCancelled.current) {
          console.clear()
          isSending.current = true
          
          // Mostra a mensagem inicial
          setCurrentAction(t('progress.status.starting'))
          
          // Calcula e mostra o relatório antes do delay
          const variaveisCount = contacts?.[0] 
            ? Object.keys(contacts[0])
                .filter(key => key.startsWith('value') || key === 'phone' || key === 'name')
                .length 
            : 0

          console.log(`
      ============================================================
                       📊 RELATÓRIO DO DISPARO 📊
      ============================================================
      
      📱 INSTÂNCIAS SELECIONADAS (${selectedInstances?.length || 0}):
      
      ${selectedInstances?.map((instance, index) => 
`      ${index + 1}. Nome: ${typeof instance === 'object' ? instance.name : instance} | Tipo: ${typeof instance === 'object' && instance.integration === 'WHATSAPP-BAILEYS' ? '📱 Baileys' : '✓ Business'}`).join('\n')}
      
      ------------------------------------------------------------
      
      📋 DADOS DO DISPARO:
      
      • Total de Contatos: ${contacts?.length || 0}
      • Variáveis Encontradas: ${variaveisCount}
      
      ------------------------------------------------------------
      
      ✉️ Conteudo:
      ${Array.isArray(message) 
        ? message.map((template, index) => `
        Template ${index + 1}:
        ${template}`).join('\n')
        : message?.trim() 
          ? `
        Template:
        "${message}"`
          : '        Nenhum template definido'}
      
      ------------------------------------------------------------
      
      📎 MÍDIA:
      
      • Status: ${mediaInfo ? 'Sim' : 'Não'}
      ${mediaInfo ? `• Arquivo: ${mediaInfo.url}
      • Tipo: ${mediaInfo.type}` : ''}
      
      ------------------------------------------------------------
      
      🤖 TYPEBOT:
        
        • Status: ${isTypebotConfigured ? 'Sim' : 'Não'}
        ${isTypebotConfigured ? `• URL: ${typebotConfig.url}
        • Bot: ${typebotConfig.typebot}` : ''}
      
      ------------------------------------------------------------
      
      ⏱️ CONFIGURAÇÃO DE TEMPO:
      
      • Mínimo: ${minTime} segundos
      • Máximo: ${maxTime} segundos
      
      ============================================================`);
            
          // Agora aguarda os 5 segundos
          await new Promise(resolve => setTimeout(resolve, 5000))
          
          if (!userCancelled.current) {
            await processNextContact()
          }
        }
      } catch (error) {
        console.error('❌ Erro ao iniciar disparo:', error)
        setCurrentAction(t('progress.status.error'))
      }
    }

    if (contacts.length > 0) {
      startDisparo()
    }

    return () => {
      isExecuting.current = false
    }
  }, [contacts.length, processNextContact, userCancelled, selectedInstances, message, mediaInfo, minTime, maxTime])

  const waitRandomTime = async () => {
    const pauseTime = Math.floor(Math.random() * (parseInt(maxTime) - parseInt(minTime) + 1)) + parseInt(minTime)
    setCurrentAction(t('progress.status.waiting', { seconds: pauseTime }))
    console.log(`⏱️ Aguardando ${pauseTime} segundos...`)
    await new Promise(resolve => setTimeout(resolve, pauseTime * 1000))
  }

  const startDisparo = async () => {
    const processedIds = new Set<string>()
    
    setCurrentAction(t('progress.status.starting'))
    console.log('🚀 Iniciando disparo em massa...')
    await new Promise(resolve => setTimeout(resolve, 5000))

    try {
      for (let i = 0; i < contacts.length; i++) {
        if (isCancelled) break
        
        const contact = contacts[i]
        
        if (processedIds.has(contact.id)) {
          console.log(`⚠️ Contato ID ${contact.id} já processado, pulando...`)
          continue
        }

        const success = await sendMessageToContact(contact)
        
        if (success) {
          processedIds.add(contact.id)
          
          if (i < contacts.length - 1) {
            await waitRandomTime()
          }
        }
      }
    } finally {
      const finalStatus = {
        total: status.total,
        enviadas: processedIds.size,
        erros: status.erros,
        pendentes: status.total - processedIds.size
      }

      setStatus(finalStatus)
      setIsComplete(true)
      
      console.log(`
        ============================================================
                        📊 RESUMO DO DISPARO 📊
        ============================================================
        • Total de mensagens: ${finalStatus.total}
        • Mensagens enviadas: ${finalStatus.enviadas}
        • Mensagens com erro: ${finalStatus.erros}
        • Mensagens não enviadas: ${finalStatus.pendentes}
        • Taxa de sucesso: ${((finalStatus.enviadas / finalStatus.total) * 100).toFixed(2)}%
        ============================================================
      `)

      setCurrentAction(isCancelled ? t('progress.status.canceled') : t('progress.status.completed'))
    }
  }

  const handleCancelDisparo = async () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
    
    // Imediatamente atualiza todos os estados necessários
    setIsCancelled(true)
    userCancelled.current = true
    isSending.current = false
    setCurrentAction(t('progress.buttons.cancel'))
    
    const pendingContacts = contacts.filter(c => !processedContacts.current.has(c.id))
    const canceledReports = pendingContacts.map(contact => ({
      numero: contact.phone,
      status: 'Cancelado' as const,
      instancia: '-',
      templateNumero: '-',
      mensagem: '-',
      enviadoEm: '-'
    }))
    
    // Atualiza todos os estados de uma vez
    setContatosData(prev => [...prev, ...canceledReports])
    setStatus(prev => ({
      ...prev,
      erros: prev.erros + prev.pendentes
    }))
    setIsComplete(true)
  }

  const handleNovoDisparo = () => {
    // Recarrega a página
    window.location.reload()
  }

  const progress = Math.min(
    ((status.total - status.pendentes) / status.total) * 100,
    100
  )

  const downloadCSV = (contatos: ContatoReport[]) => {
    try {
      const headers = [
        `${t('progress.report.csv.phone')}`,
        `${t('progress.report.csv.status')}`,
        `${t('progress.report.csv.instance')}`,
        `${t('progress.report.csv.template')}`,
        `${t('progress.report.csv.message')}`,
        `${t('progress.report.csv.sent_at')}`,
        `${t('progress.report.csv.agent')}`,
        `${t('progress.report.csv.labels')}`
      ];

      const csvContent = [
        headers.join(','),
        ...contatos.map(contato => [
          contato.numero,
          contato.status,
          contato.instancia,
          contato.templateNumero,
          `"${contato.mensagem.replace(/"/g, '""')}"`,
          contato.enviadoEm || '-',
          contato.agente || '-',
          contato.labels || '-'
        ].join(','))
      ].join('\n');

      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const filename = `${t('progress.report.csv.filename')}-${new Date().toISOString().slice(0,10)}.csv`;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Erro ao gerar CSV:', error);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-black">
      <Header />
      <div className="flex-grow flex items-center justify-center p-4">
        <Card className="w-full max-w-xl bg-zinc-950 border-zinc-900 shadow-2xl">
          <CardHeader className="border-b border-zinc-900 pb-4">
            <CardTitle className="text-2xl font-bold text-center text-zinc-100 flex items-center justify-center">
              <MessageCircle className="mr-2 text-emerald-500 h-6 w-6" />
              {t('progress.title')}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-6">
            <div className="space-y-2">
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 transition-all duration-500 ease-in-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-zinc-400">{currentAction}</span>
                <span className="text-emerald-400 font-bold">{Math.round(progress)}%</span>
              </div>
            </div>

            {!isComplete && !isCancelled && (
              <div className="grid grid-cols-2 gap-4">
                <StatusItem
                  icon={<Clock className="text-blue-400 h-5 w-5" />}
                  label={t('progress.stats.pending')}
                  value={status.pendentes}
                  total={status.total}
                  color="blue"
                />
                <StatusItem
                  icon={<CheckCircle className="text-emerald-400 h-5 w-5" />}
                  label={t('progress.stats.sent')}
                  value={status.enviadas}
                  total={status.total}
                  color="emerald"
                />
                <StatusItem
                  icon={<XCircle className="text-red-400 h-5 w-5" />}
                  label={t('progress.stats.errors')}
                  value={status.erros}
                  total={status.total}
                  color="red"
                />
                <StatusItem
                  icon={<AlertCircle className="text-yellow-400 h-5 w-5" />}
                  label={t('progress.stats.total')}
                  value={status.total}
                  total={status.total}
                  color="yellow"
                />
              </div>
            )}
            {(isComplete || isCancelled) && (
              <div className="bg-zinc-900 p-4 rounded-lg">
                <h3 className="text-zinc-100 font-bold mb-2 flex items-center">
                  {!isCancelled ? (
                    <CheckCircle className="text-green-500 h-5 w-5 mr-2" />
                  ) : (
                    <StopCircle className="text-red-500 h-5 w-5 mr-2" />
                  )}
                  {!isCancelled ? t('progress.summary.title') : t('progress.summary.canceled_title')}
                </h3>
                <ul className="text-zinc-300 text-sm space-y-1">
                  <li>{t('progress.summary.total_messages')}: {status.total}</li>
                  <li>{t('progress.summary.sent_messages')}: {status.enviadas}</li>
                  <li>{t('progress.summary.error_messages')}: {status.erros}</li>
                  <li>{t('progress.summary.unsent_messages')}: {status.pendentes}</li>
                  <li>{t('progress.summary.success_rate')}: {((status.enviadas / status.total) * 100).toFixed(2)}%</li>
                </ul>
                <Button
                  onClick={() => downloadCSV(contatosData)}
                  className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded-full transition-all duration-300 transform hover:scale-105 hover:shadow-lg text-sm"
                >
                  {t('progress.buttons.download')}
                  <DownloadIcon className="ml-2 h-4 w-4" />
                </Button>
              </div>
            )}
          </CardContent>
          <CardFooter className="flex flex-col items-center border-t border-zinc-900 pt-4 mt-2">
            {!isComplete && !isCancelled && (
              <Button
                onClick={handleCancelDisparo}
                className="w-full max-w-md bg-red-600 hover:bg-red-700 text-white font-bold py-2 rounded-full transition-all duration-300 transform hover:scale-105 hover:shadow-lg text-sm"
              >
                {t('progress.buttons.cancel')}
                <StopCircle className="ml-2 h-4 w-4" />
              </Button>
            )}
            {(isComplete || isCancelled) && (
              <Button
                onClick={handleNovoDisparo}
                className="w-full max-w-md bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 rounded-full transition-all duration-300 transform hover:scale-105 hover:shadow-lg text-sm"
              >
                {t('progress.buttons.new')}
                <RefreshCw className="ml-2 h-4 w-4" />
              </Button>
            )}
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}

interface StatusItemProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  total: number;
  color: 'blue' | 'emerald' | 'red' | 'yellow';
}

const StatusItem: React.FC<StatusItemProps> = ({ icon, label, value, total, color }) => {
  const percentage = (value / total) * 100;
  const colorClasses = {
    blue: 'bg-blue-400',
    emerald: 'bg-emerald-400',
    red: 'bg-red-400',
    yellow: 'bg-yellow-400'
  };

  return (
    <div className="bg-zinc-900 p-3 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          {icon}
          <span className="text-zinc-300 text-sm ml-2">{label}</span>
        </div>
        <span className="text-zinc-100 font-bold">{value}</span>
      </div>
      <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClasses[color]} transition-all duration-500 ease-in-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

interface Contact {
  id: string;
  phone: string;
  name: string;
  [key: string]: string;
}

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

function formatarNumeroChatwoot(numero: string): string {
  // Remove qualquer caractere que não seja número
  const numeroLimpo = numero.replace(/\D/g, '')
  
  // Extrai o DDD (posições 2 e 3 após o 55)
  const ddd = numeroLimpo.substring(2, 4)
  
  // Extrai o resto do número após o DDD
  const restante = numeroLimpo.substring(4)
  
  let numeroFormatado: string

  // Se DDD >= 31, remove o 9 se existir
  if (parseInt(ddd) >= 31) {
    numeroFormatado = restante.startsWith('9') 
      ? `55${ddd}${restante.substring(1)}` // Remove o 9
      : numeroLimpo
  } 
  // Se DDD <= 30, adiciona o 9 se não existir
  else {
    numeroFormatado = !restante.startsWith('9') 
      ? `55${ddd}9${restante}` // Adiciona o 9
      : numeroLimpo
  }

  return numeroFormatado
}

async function processarContato(contato: Contato, instancia: Instancia) {
  try {
    console.log(`📱 Iniciando envio para ${contato.numero} usando instância ${instancia.nome}`)
    
    // Envio da mensagem
    const response = await enviarMensagem(contato, instancia)
    console.log('📨 Resposta da Evolution:', response)
    
    if (response.success) {
      console.log(`✅ Mensagem enviada com sucesso para ${contato.numero}`)
      
      try {
        // Formata o número para busca no Chatwoot
        const numeroFormatado = formatarNumeroChatwoot(contato.numero)
        console.log(`\n🔍 Iniciando busca no Chatwoot:`)
        console.log(`• Número original: ${contato.numero}`)
        console.log(`• Número formatado: ${numeroFormatado}`)
        
        const contatoResponse = await fetch(`/api/chatwoot/contacts/search?q=${numeroFormatado}`)
        const contatoData = await contatoResponse.json()
        
        if (contatoData.payload?.length > 0) {
          const contatoId = contatoData.payload[0].id
          console.log(`✅ Contato encontrado no Chatwoot. ID: ${contatoId}`)
          
          // ... resto do código
        } else {
          console.error('❌ Contato não encontrado no Chatwoot')
        }
      } catch (error) {
        console.error('❌ Erro no processo de atribuição:', error)
      }
    } else {
      console.error('❌ Erro ao enviar mensagem:', response.error)
    }
  } catch (error) {
    console.error('❌ Erro ao processar contato:', error)
  }
}