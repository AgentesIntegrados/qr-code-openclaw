'use client'

import { Contact } from "@/types"
import { useEffect, useState } from 'react';
import { useTranslation } from '@/hooks/useTranslation'

interface VariablesPopoverProps {
  onSelectVariable: (variable: string) => void
  contacts: Contact[]
}

export function VariablesPopover({ onSelectVariable, contacts }: VariablesPopoverProps) {
  const { t } = useTranslation()
  const [variables, setVariables] = useState<{ key: string; value: string }[]>([]);
  const [showVariables, setShowVariables] = useState(false);

  // Função para obter as variáveis disponíveis a partir dos contatos
  useEffect(() => {
    const availableVariables = contacts.map(contact => ({
      key: contact.phone,
      value: contact.name
    })).filter(variable => variable.value); // Filtra apenas as variáveis com valor

    setVariables(availableVariables);
  }, [contacts]);

  // Contagem de variáveis disponíveis
  const availableVariablesCount = variables.filter(variable => variable.value).length; 

  const exampleContact = contacts[0] || {}

  const getAvailableVariables = () => {
    const variables = []

    Object.entries(exampleContact).forEach(([key, value]) => {
      // Ignora a variável "id" e outras que começam com "contact_"
      if (value && !key.startsWith('contact_') && key !== 'id') {
        const displayValue = typeof value === 'string' 
          ? (value.length > 15 ? value.substring(0, 15) + '...' : value)
          : value.toString();

        const keyMap: { [key: string]: string } = {
          name: 'nome',
          phone: 'numero',
          value1: 'valor1',
          value2: 'valor2',
          value3: 'valor3',
          value4: 'valor4',
          value5: 'valor5'
        };

        const displayKey = keyMap[key] || key;
        variables.push({ key: displayKey, value: displayValue });
      }
    });

    return variables;
  }

  const availableVariables = getAvailableVariables();

  // Filtra as variáveis para garantir que não haja duplicatas
  const uniqueVariables = Array.from(new Set(availableVariables.map(v => v.key)))
    .map(key => availableVariables.find(v => v.key === key));

  return (
    <div className="bg-zinc-800/80 rounded-md p-3 space-y-2">
      <p className="text-sm text-zinc-400">
        {t('message_composition.variables.help_text')}
      </p>
      <div className="flex flex-wrap gap-2">
        {uniqueVariables.map(({ key, value }) => (
          <button
            key={key}
            onClick={() => onSelectVariable(`[${key}]`)}
            className="px-2 py-1 bg-zinc-900 hover:bg-zinc-800 
                     border border-zinc-700 rounded-md text-zinc-300 
                     hover:text-zinc-100 transition-colors text-sm"
          >
            {value}
          </button>
        ))}
      </div>
    </div>
  );
}
