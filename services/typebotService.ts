export const startTypebot = async (
  instance: string,
  url: string,
  bot: string,
  number: string,
  variables: Record<string, string>[]
) => {
  const baseUrl = process.env.NEXT_PUBLIC_EVOLUTION_URL;
  const apikey = process.env.NEXT_PUBLIC_EVOLUTION_API;

  const payload = {
    url,
    typebot: bot,
    remoteJid: `${number}@s.whatsapp.net`,
    startSession: true,
    variables: Object.entries(variables).map(([name, value]) => ({
      name,
      value
    }))
  };

  console.log('Dados enviados para o Typebot:', {
    instance,
    url,
    bot,
    number,
    variables: payload.variables
  });

  const response = await fetch(`${baseUrl}/typebot/start/${instance}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': apikey
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Erro ao iniciar o Typebot: ${response.status} ${response.statusText}`);
  }

  return response;
};
