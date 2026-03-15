import { NextResponse } from 'next/server'
import { Pool } from 'pg'

const pool = new Pool({
  connectionString: process.env.NEXT_PUBLIC_CHATWOOT_DATABASE_CONNECTION_URI
})

export async function GET() {
  try {
    console.log('🔍 Iniciando busca de labels no banco...')
    
    const query = `
      SELECT 
        title,
        description,
        color
      FROM 
        labels 
      WHERE 
        account_id = $1
      ORDER BY
        title ASC
    `

    const result = await pool.query(query, [process.env.NEXT_PUBLIC_CHATWOOT_ACCOUNT_ID])
    console.log('✅ Labels encontradas:', result.rows)

    return NextResponse.json({
      success: true,
      payload: result.rows
    })
  } catch (error) {
    console.error('❌ Erro ao buscar labels:', error)
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Erro desconhecido ao buscar labels'
      },
      { status: 500 }
    )
  }
} 