import { NextResponse } from 'next/server'
import { hash, compare } from '@/utils/crypto'

export async function POST(request: Request) {
  try {
    const { username, password } = await request.json()
    
    const validUsername = process.env.NEXT_PUBLIC_AUTH_USERNAME
    const validPassword = process.env.NEXT_PUBLIC_AUTH_PASSWORD
    
    if (!validUsername || !validPassword) {
      return NextResponse.json(
        { error: 'Configuração de autenticação inválida' },
        { status: 500 }
      )
    }

    if (username === validUsername && password === validPassword) {
      const token = hash(`${username}:${Date.now()}`)
      return NextResponse.json({ token })
    }

    return NextResponse.json(
      { error: 'Credenciais inválidas' },
      { status: 401 }
    )
  } catch (error) {
    console.error('Erro na autenticação:', error)
    return NextResponse.json(
      { error: 'Erro interno' },
      { status: 500 }
    )
  }
}
