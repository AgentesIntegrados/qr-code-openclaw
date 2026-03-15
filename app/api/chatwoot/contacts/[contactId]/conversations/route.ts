import { NextRequest } from 'next/server'

export async function GET(
  request: NextRequest,
  context: { params: { contactId: string } }
) {
  try {
    const { contactId } = await context.params
    
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_CHATWOOT_DOMAIN}/api/v1/accounts/${process.env.NEXT_PUBLIC_CHATWOOT_ACCOUNT_ID}/contacts/${contactId}/conversations`,
      {
        headers: {
          'api_access_token': process.env.NEXT_PUBLIC_CHATWOOT_TOKEN as string,
          'Content-Type': 'application/json'
        }
      }
    )
    
    const data = await response.json()
    return Response.json(data)
  } catch (error) {
    console.error('Erro ao buscar conversas:', error)
    return Response.json({ error: 'Erro ao buscar conversas' }, { status: 500 })
  }
} 