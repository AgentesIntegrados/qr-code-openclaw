import crypto from 'crypto';
import fs from 'fs'
import path from 'path'

export const uploadMedia = async (file: File, newFileName: string) => {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error('Falha ao fazer upload da mídia')
    }

    const data = await response.json()
    return {
      url: data.url,
      type: file.type,
      name: data.filename
    }
  } catch (error) {
    console.error('Erro no upload:', error)
    throw error
  }
}

export const sendMediaMessage = async (
  number: string, 
  mediaInfo: { url: string; type: string; name: string },
  text: string,
  instanceName: string,
  apikey: string,
  baseUrl: string
) => {
  const mediaPayload = {
    number,
    mediatype: mediaInfo.type.startsWith('image/') ? 'image' : 'document',
    caption: text,
    media: mediaInfo.url
  }

  const response = await fetch(`${baseUrl}/message/sendMedia/${instanceName}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': apikey
    },
    body: JSON.stringify(mediaPayload)
  })

  if (!response.ok) {
    throw new Error(`Erro ao enviar mídia: ${response.status}`)
  }

  return response
}
