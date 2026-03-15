import { NextResponse } from 'next/server'
import { writeFile } from 'fs/promises'
import path from 'path'
import crypto from 'crypto'

export async function POST(request: Request) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File

    if (!file) {
      return NextResponse.json(
        { error: 'Nenhum arquivo enviado' },
        { status: 400 }
      )
    }

    const hash = crypto
      .createHash('md5')
      .update(`${file.name}${Date.now()}`)
      .digest('hex')
      .substring(0, 8)

    const ext = path.extname(file.name)
    const filename = `${hash}${ext}`

    const buffer = Buffer.from(await file.arrayBuffer())
    const publicPath = path.join(process.cwd(), 'public', 'uploads')
    const filePath = path.join(publicPath, filename)

    await writeFile(filePath, buffer)

    return NextResponse.json({
      url: `/uploads/${filename}`,
      filename: filename,
      type: file.type
    })
  } catch (error) {
    console.error('Erro no upload:', error)
    return NextResponse.json(
      { error: 'Erro ao processar upload' },
      { status: 500 }
    )
  }
}
