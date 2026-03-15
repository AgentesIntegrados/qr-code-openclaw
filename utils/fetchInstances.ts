'use client'

export const fetchInstances = async () => {
  const baseUrl = process.env.NEXT_PUBLIC_EVOLUTION_URL?.replace(/\/$/, '')
  const url = `${baseUrl}/instance/fetchInstances`
  const apiKey = process.env.NEXT_PUBLIC_EVOLUTION_API

  if (!baseUrl || !apiKey) {
    throw new Error('Configuração incompleta')
  }

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'apikey': apiKey,
      },
    })

    if (!response.ok) {
      throw new Error('Failed to fetch instances')
    }

    const data = await response.json()

    const filteredInstances = data.filter((instance: any) => 
      instance.connectionStatus === 'open' && 
    // (instance.integration === 'WHATSAPP-BAILEYS' || instance.integration === 'WHATSAPP-BUSINESS')
    (instance.integration === 'WHATSAPP-BAILEYS')
    ).map((instance: any) => ({
      id: instance.id,
      name: instance.name,
      ownerJid: instance.ownerJid,
      integration: instance.integration
    }))

    console.log(`
      ============================================================
                    🟢 INSTÂNCIAS ENCONTRADAS 🟢
      ============================================================

      Total de Instâncias: ${filteredInstances.length}

      ------------------------------------------------------------
      ${filteredInstances.map((instance, index) => `
       ${index + 1}. Nome        : ${instance.name}
          Tipo        : ${instance.integration === 'WHATSAPP-BAILEYS' ? '📱 Baileys' : '✓ Business'}
          ID do Dono  : ${instance.ownerJid}
          
      ------------------------------------------------------------
      `
      ).join('')}
      ============================================================
      `);

    return filteredInstances
  } catch (error) {
    throw new Error('Erro ao carregar instâncias. Por favor, tente novamente.')
  }
}
