interface Contact {
  phone: string
  name: string
  value1?: string
  value2?: string
  value3?: string
}

export interface Instance {
  id: string
  name: string
  ownerJid: string
  // integration: 'WHATSAPP-BAILEYS' | 'WHATSAPP-BUSINESS'
  integration: 'WHATSAPP-BAILEYS'
}

export interface Agent {
  id: number
  name: string
  // ... outros campos necessários ...
}
