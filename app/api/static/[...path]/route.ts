import { NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import path from 'path'

export async function GET(
  request: Request,
  { params }: { params: { path: string[] } }
) {
  try {
    const filePath = path.join(process.cwd(), 'public', 'uploads', ...params.path)
    const fileBuffer = await readFile(filePath)
    
    const contentType = path.extname(filePath) === '.jpeg' || path.extname(filePath) === '.jpg' 
      ? 'image/jpeg'
      : 'application/octet-stream'

    return new NextResponse(fileBuffer, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=31536000',
      },
    })
  } catch (error) {
    console.error('Erro ao servir arquivo:', error)
    return new NextResponse('Arquivo não encontrado', { status: 404 })
  }
}
