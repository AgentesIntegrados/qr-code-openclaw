'use client'

import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, Smartphone, RefreshCw, CheckCircle, XCircle, LogOut } from 'lucide-react'

type Status = 'idle' | 'checking' | 'connected' | 'disconnected' | 'connecting' | 'error'

export default function QRCodePage() {
  const [status, setStatus] = useState<Status>('checking')
  const [qrCode, setQrCode] = useState('')
  const [message, setMessage] = useState('')
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    checkStatus()
    return () => {
      eventSourceRef.current?.close()
    }
  }, [])

  const checkStatus = async () => {
    setStatus('checking')
    try {
      const res = await fetch('/api/whatsapp/status')
      const data = await res.json()
      setStatus(data.connected ? 'connected' : 'disconnected')
      setMessage(data.connected ? 'WhatsApp conectado' : '')
    } catch {
      setStatus('disconnected')
    }
  }

  const startConnection = () => {
    eventSourceRef.current?.close()
    setStatus('connecting')
    setQrCode('')
    setMessage('Gerando QR Code...')

    const es = new EventSource('/api/whatsapp/connect')
    eventSourceRef.current = es

    es.addEventListener('qr', (e) => {
      const data = JSON.parse(e.data)
      setQrCode(data.qr)
      setMessage('Escaneie o QR Code com seu WhatsApp')
    })

    es.addEventListener('connected', (e) => {
      const data = JSON.parse(e.data)
      setStatus('connected')
      setQrCode('')
      setMessage(data.message || 'WhatsApp conectado com sucesso!')
      es.close()
    })

    es.addEventListener('error', (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data)
        setMessage(data.message || 'Erro na conexao')
      } catch {
        setMessage('Conexao com servidor perdida')
      }
      setStatus('error')
      es.close()
    })

    es.addEventListener('done', () => {
      checkStatus()
      es.close()
    })

    es.onerror = () => {
      if (es.readyState === EventSource.CLOSED) return
      setStatus('error')
      setMessage('Conexao com servidor perdida')
      es.close()
    }
  }

  const disconnect = async () => {
    setStatus('checking')
    setMessage('Desconectando...')
    try {
      await fetch('/api/whatsapp/disconnect', { method: 'POST' })
      setStatus('disconnected')
      setQrCode('')
      setMessage('Desconectado')
    } catch {
      setMessage('Erro ao desconectar')
      setStatus('error')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl font-bold flex items-center gap-2">
              <Smartphone className="h-6 w-6" />
              Conectar WhatsApp
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center space-y-6">
              {status === 'checking' && (
                <div className="py-12">
                  <Loader2 className="h-12 w-12 animate-spin mx-auto text-gray-400" />
                  <p className="mt-4 text-gray-600">Verificando status...</p>
                </div>
              )}

              {status === 'connected' && (
                <div className="py-12">
                  <CheckCircle className="h-16 w-16 text-green-500 mx-auto" />
                  <p className="mt-4 text-lg font-medium text-green-600">{message}</p>
                  <div className="mt-6 flex gap-3 justify-center">
                    <Button onClick={checkStatus} variant="outline">
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Atualizar
                    </Button>
                    <Button onClick={disconnect} variant="destructive">
                      <LogOut className="mr-2 h-4 w-4" />
                      Desconectar
                    </Button>
                  </div>
                </div>
              )}

              {status === 'disconnected' && (
                <div className="py-12">
                  <XCircle className="h-16 w-16 text-gray-400 mx-auto" />
                  <p className="mt-4 text-gray-600">WhatsApp desconectado</p>
                  <Button onClick={startConnection} className="mt-6">
                    <Smartphone className="mr-2 h-4 w-4" />
                    Conectar WhatsApp
                  </Button>
                </div>
              )}

              {status === 'connecting' && (
                <div className="py-6">
                  {qrCode ? (
                    <>
                      <p className="mb-4 font-medium">{message}</p>
                      <div className="inline-block bg-black rounded-lg p-2 shadow-lg">
                        <pre
                          className="text-white leading-none"
                          style={{
                            fontSize: '4px',
                            lineHeight: '4px',
                            letterSpacing: '0px',
                            fontFamily: 'monospace',
                          }}
                        >
                          {qrCode}
                        </pre>
                      </div>
                      <p className="mt-4 text-sm text-gray-500">
                        Abra o WhatsApp &gt; Aparelhos conectados &gt; Conectar aparelho
                      </p>
                      <Button onClick={startConnection} variant="outline" className="mt-4">
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Gerar Novo QR Code
                      </Button>
                    </>
                  ) : (
                    <>
                      <Loader2 className="h-12 w-12 animate-spin mx-auto text-gray-400" />
                      <p className="mt-4 text-gray-600">{message}</p>
                    </>
                  )}
                </div>
              )}

              {status === 'error' && (
                <div className="py-12">
                  <XCircle className="h-16 w-16 text-red-400 mx-auto" />
                  <p className="mt-4 text-red-600">{message}</p>
                  <div className="mt-6 flex gap-3 justify-center">
                    <Button onClick={startConnection}>
                      Tentar Novamente
                    </Button>
                    <Button onClick={checkStatus} variant="outline">
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Verificar Status
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
