import { NextRequest } from 'next/server'

export async function POST(
  request: NextRequest,
  context: { params: { conversationId: string } }
) {
  try {
    const { conversationId } = await context.params
    const body = await request.json()
    
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_CHATWOOT_DOMAIN}/api/v1/accounts/${process.env.NEXT_PUBLIC_CHATWOOT_ACCOUNT_ID}/conversations/${conversationId}/assignments`,
      {
        method: 'POST',
        headers: {
          'api_access_token': process.env.NEXT_PUBLIC_CHATWOOT_TOKEN as string,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      }
    )
    
    const data = await response.json()
    return Response.json(data)
  } catch (error) {
    console.error('Erro ao atribuir conversa:', error)
    return Response.json({ error: 'Erro ao atribuir conversa' }, { status: 500 })
  }
} 