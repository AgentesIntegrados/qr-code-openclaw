export const sendMediaMessage = async (
  phone: string,
  mediaInfo: { url: string; type: string; name: string },
  processedMessage: string,
  instanceName: string,
  apikey: string,
  baseUrl: string
) => {
  const mediaPayload = {
    number: phone,
    mediatype: mediaInfo.type.startsWith('image/') ? 'image' : mediaInfo.type.startsWith('video/') ? 'video' : 'document',
    mimetype: mediaInfo.type,
    caption: processedMessage,
    media: mediaInfo.url,
    fileName: mediaInfo.name
  };

  const response = await fetch(`${baseUrl}/message/sendMedia/${instanceName}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': apikey
    },
    body: JSON.stringify(mediaPayload)
  });

  if (!response.ok) {
    throw new Error(`Erro ao enviar mídia: ${response.status} ${response.statusText}`);
  }

  return response;
};
