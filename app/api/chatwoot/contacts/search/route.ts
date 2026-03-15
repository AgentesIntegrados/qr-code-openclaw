import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const query = searchParams.get('q')

  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_CHATWOOT_DOMAIN}/api/v1/accounts/${process.env.NEXT_PUBLIC_CHATWOOT_ACCOUNT_ID}/contacts/search?q=${query}`,
      {
        headers: {
          'api_access_token': process.env.NEXT_PUBLIC_CHATWOOT_TOKEN,
          'Content-Type': 'application/json'
        }
      }
    )

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Erro ao buscar contato' }, { status: 500 })
  }
} 