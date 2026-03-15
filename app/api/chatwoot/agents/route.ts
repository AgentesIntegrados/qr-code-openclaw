import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_CHATWOOT_DOMAIN}/api/v1/accounts/${process.env.NEXT_PUBLIC_CHATWOOT_ACCOUNT_ID}/agents`,
      {
        headers: {
          'api_access_token': process.env.NEXT_PUBLIC_CHATWOOT_TOKEN,
          'Content-Type': 'application/json'
        },
        cache: 'no-store'
      }
    )

    if (!response.ok) {
      throw new Error('Erro ao buscar agentes')
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Erro:', error)
    return NextResponse.json({ error: 'Erro ao buscar agentes' }, { status: 500 })
  }
}