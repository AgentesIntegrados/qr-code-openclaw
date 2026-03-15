'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Upload, ChevronRight, Users, Download } from 'lucide-react'
import type { Contact, Instance } from "@/types"
import { useTranslation } from '@/hooks/useTranslation'
import { parsePhoneNumber } from 'libphonenumber-js'

interface EntradaContatosProps {
  selectedInstances: Instance[]
  onNextStep: (contacts: Contact[]) => void
}

const autoFillDdi = process.env.NEXT_PUBLIC_AUTO_FILL_DDI === 'true'
const defaultLocation = process.env.NEXT_PUBLIC_DEFAULT_LOCATION || 'BR'

export function EntradaContatosComponent({ selectedInstances, onNextStep }: EntradaContatosProps) {
  const { t } = useTranslation()
  const [manualInput, setManualInput] = useState('')
  const [contacts, setContacts] = useState<Contact[]>([])
  const [activeTab, setActiveTab] = useState('manual')

  useEffect(() => {
    console.clear()
    console.log(`
      ============================================================
                    ✅ INSTÂNCIAS SELECIONADAS ✅
      ============================================================

      Total de Instâncias Selecionadas: ${selectedInstances.length}

      ------------------------------------------------------------
      ${selectedInstances.map((instance, index) => `
       ${index + 1}. Nome        : ${instance.name}
          Tipo        : ${instance.integration === 'WHATSAPP-BAILEYS' ? '📱 Baileys' : '✓ Business'}
      ${index < selectedInstances.length - 1 ? '------------------------------------------------------------' : ''}
      `).join('')}
      ============================================================
  `);
  }, []);

  const parseManualInput = (input: string): Contact[] => {
    return input
      .split('\n')
      .filter(line => line.trim())
      .map((line, index) => {
        const values = line.split(',').map(item => item.trim());
        const phone = values[0] || '';
        let formattedPhone = phone;

        if (autoFillDdi && phone.length >= 10 && phone.length <= 15 && !phone.endsWith('@g.us')) {
          try {
            const phoneNumber = parsePhoneNumber(phone, defaultLocation);
            formattedPhone = phoneNumber.number;
          } catch (error) {
            console.error('Erro ao formatar número:', error);
          }
        }

        const contact: Contact = {
          id: `contact_${index + 1}`,
          phone: formattedPhone,
          name: values[1] || '',
        };

        values.slice(2).forEach((value, index) => {
          if (value) {
            contact[`value${index + 1}`] = value;
          }
        });

        return contact;
      });
  };

  const handleManualInputChange = (value: string) => {
    setManualInput(value)
    setContacts(parseManualInput(value))
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const content = e.target?.result as string
        const lines = content.split('\n')
        const dataWithoutHeader = lines.slice(1).join('\n')
        setManualInput(dataWithoutHeader)
        setContacts(parseManualInput(dataWithoutHeader))
        setActiveTab('manual')
      }
      reader.readAsText(file)
    }
  }

  const handleNextStep = () => {
    onNextStep(contacts)
  }

  const downloadExampleCSV = () => {
    const csvContent = [
      ['Número', 'Nome', 'Profissão', 'Experiência', 'Estado'],
      ['5511973052593', 'Ana Pereira', 'Analista de Marketing', '5 anos', 'Minas Gerais'],
      ['5511973052593', 'Lucas Almeida', 'Engenheiro de Software', '2 anos', 'Rio de Janeiro']
    ].map(row => row.join(',')).join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', 'exemplo-contatos.csv')
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="flex flex-col min-h-screen bg-black">
      <div className="flex-grow flex items-center justify-center p-4">
        <Card className="w-full max-w-xl bg-zinc-950 border-zinc-900 shadow-2xl">
          <CardHeader className="border-b border-zinc-900 pb-4">
            <CardTitle className="text-2xl font-bold text-center text-zinc-100 flex items-center justify-center">
              <Users className="mr-2 text-emerald-500 h-5 w-5" />
              {t('contacts.title')}
            </CardTitle>
            <p className="text-zinc-400 text-center mt-1 text-sm">
              {t('contacts.subtitle')}
            </p>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="mb-4">
              <div className="flex w-full p-1 bg-zinc-900/50 border border-zinc-800 rounded-lg">
                <button
                  onClick={() => setActiveTab('manual')}
                  className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'manual'
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'text-zinc-400 hover:text-zinc-300'
                  }`}
                >
                  {t('contacts.tabs.manual')}
                </button>
                <button
                  onClick={() => setActiveTab('csv')}
                  className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'csv'
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'text-zinc-400 hover:text-zinc-300'
                  }`}
                >
                  {t('contacts.tabs.csv')}
                </button>
              </div>
            </div>
            
            <div className="h-[350px] mt-6">
              {activeTab === 'csv' ? (
                <label
                  htmlFor="csv-upload"
                  className="flex flex-col items-center justify-center h-full w-full border-2 border-dashed border-zinc-800/50 rounded-lg bg-zinc-900/50 cursor-pointer"
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                  }}
                  onDrop={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                      handleFileUpload({ target: { files } });
                    }
                  }}
                >
                  <Upload className="h-8 w-8 text-zinc-700 mb-2" />
                  <p className="text-sm text-zinc-500 mb-6">
                    {t('contacts.upload.title')}
                  </p>
                  <Button
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      downloadExampleCSV();
                    }}
                    className="flex items-center gap-2 bg-[#18181b] border border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-white transition duration-200 px-4 py-2 rounded-md"
                  >
                    <Download className="h-4 w-4" />
                    {t('contacts.upload.button')}
                  </Button>
                  <input
                    id="csv-upload"
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>
              ) : (
                <Textarea
                  placeholder={t('contacts.manual.placeholder')}
                  value={manualInput}
                  onChange={(e) => handleManualInputChange(e.target.value)}
                  className="h-full bg-zinc-900/50 border-zinc-800 text-white resize-none"
                />
              )}
            </div>
          </CardContent>
          <CardFooter className="flex flex-col items-center border-t border-zinc-900 pt-4">
            <p className="text-zinc-500 mb-3 text-sm">
              {t('contacts.status.contacts_count').replace('{count}', contacts.length.toString())}
            </p>
            <Button 
              onClick={handleNextStep} 
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 rounded-full transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              disabled={contacts.length === 0}
            >
              {t('contacts.buttons.next')}
              <ChevronRight className="ml-2 h-4 w-4" />
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}