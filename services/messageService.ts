import { parsePhoneNumber } from 'libphonenumber-js';

export const sendMessage = async (
  number: string, 
  text: string, 
  instanceName: string,
  variables?: Record<string, string>
) => {
  let formattedNumber = number;

  const autoFillDdi = process.env.NEXT_PUBLIC_AUTO_FILL_DDI === 'true';
  const defaultLocation = process.env.NEXT_PUBLIC_DEFAULT_LOCATION || 'BR';

  if (autoFillDdi && number.length <= 15 && !number.endsWith('@g.us')) {
    try {
      const phoneNumber = parsePhoneNumber(number, defaultLocation);
      formattedNumber = phoneNumber.number; // Retorna o número formatado com o DDI correto
    } catch (error) {
      console.error('Erro ao formatar número:', error);
    }
  }

  const processedText = variables ? 
    text.replace(/\[(\w+)\]/g, (match, variable) => {
      const value = variables[variable];
      return value || match;
    }) : 
    text;

  const baseUrl = process.env.NEXT_PUBLIC_EVOLUTION_URL;
  const apikey = process.env.NEXT_PUBLIC_EVOLUTION_API;
  const url = `${baseUrl}/message/sendText/${instanceName}`;
  
  if (!baseUrl || !apikey) {
    throw new Error('Configuração da API Evolution ausente. Verifique o arquivo .env');
  }
  
  const payload = {
    number: formattedNumber,
    text: processedText,
    options: {
      delay: 1200,
      presence: "composing"
    }
  };

  console.log('📤 Enviando mensagem:', {
    url,
    instanceName,
    number: formattedNumber,
    textPreview: processedText.substring(0, 50) + '...',
    hasApiKey: !!apikey
  });

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': apikey
      },
      body: JSON.stringify(payload)
    });

    const responseText = await response.text();
    
    if (!response.ok) {
      let errorDetails = '';
      try {
        const errorJson = JSON.parse(responseText);
        errorDetails = errorJson.message || errorJson.error || errorJson.response?.message || responseText;
      } catch {
        errorDetails = responseText;
      }
      
      console.error('❌ Erro detalhado da API Evolution:', {
        status: response.status,
        statusText: response.statusText,
        errorDetails,
        url,
        instanceName,
        number: formattedNumber
      });
      
      // Mensagem de erro mais específica baseada no status
      let userMessage = '';
      if (response.status === 500) {
        userMessage = 'Erro interno da API. Verifique se a instância está conectada ao WhatsApp.';
      } else if (response.status === 404) {
        userMessage = `Instância "${instanceName}" não encontrada na API.`;
      } else if (response.status === 401) {
        userMessage = 'API Key inválida. Verifique a configuração.';
      } else {
        userMessage = errorDetails;
      }
      
      throw new Error(`Erro ao enviar mensagem: ${response.status} - ${userMessage}`);
    }

    console.log('✅ Mensagem enviada com sucesso:', {
      number: formattedNumber,
      instanceName
    });

    return response;
  } catch (error) {
    console.error('❌ Erro ao enviar mensagem:', error);
    throw error;
  }
};
