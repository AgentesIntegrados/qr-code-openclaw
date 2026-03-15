import { spawn, execFile } from 'child_process'
import { promisify } from 'util'

const execFileAsync = promisify(execFile)

export const dynamic = 'force-dynamic'

export async function GET() {
  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    start(controller) {
      function send(event: string, data: any) {
        controller.enqueue(
          encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
        )
      }

      // Use openclaw channels login instead of wacli directly
      const proc = spawn('openclaw', ['channels', 'login', '--channel', 'whatsapp'], {
        env: {
          ...process.env,
          HOME: process.env.HOME || '/root',
        },
      })

      let qrLines: string[] = []
      let capturing = false
      let sent = false

      function processLine(line: string) {
        // Strip ANSI escape codes and carriage returns
        const clean = line.replace(/\x1b\[[0-9;]*[a-zA-Z]/g, '').replace(/\r/g, '').trim()
        if (!clean) return

        // Detect QR start: line of ▄ chars (openclaw format) or █ chars (wacli format)
        if (!capturing && (/^[▄]{10,}$/.test(clean) || /^[█]{10,}$/.test(clean))) {
          capturing = true
          qrLines = [clean]
          return
        }

        if (capturing) {
          // If line has block chars, it's part of the QR
          if (/[█▄▀]/.test(clean)) {
            qrLines.push(clean)
          } else {
            // Non-block line means QR is done
            if (qrLines.length > 5) {
              send('qr', { qr: qrLines.join('\n') })
              sent = true
            }
            qrLines = []
            capturing = false
            // Send this non-QR line as log
            send('log', { text: clean })
          }
          return
        }

        // Only send non-QR lines as logs
        send('log', { text: clean })

        if (/scan this qr/i.test(clean)) return

        if (/linked|logged in|successfully|paired|authenticated|syncing|sync complete|bootstrap/i.test(clean)) {
          send('connected', { message: clean })
          // Restart gateway so OpenClaw picks up the new session
          send('log', { text: 'Reiniciando gateway...' })
          execFileAsync('openclaw', ['gateway', 'restart'], { timeout: 30000 })
            .then(() => send('log', { text: 'Gateway reiniciado com sucesso!' }))
            .catch(() => send('log', { text: 'Aviso: falha ao reiniciar gateway' }))
        }

        if (/failed|error|timeout/i.test(clean) && !sent) {
          send('error', { message: clean })
        }
      }

      let buffer = ''
      function onData(chunk: Buffer) {
        buffer += chunk.toString()
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          processLine(line)
        }
      }

      proc.stdout.on('data', onData)
      proc.stderr.on('data', onData)

      proc.on('close', (code) => {
        if (capturing && qrLines.length > 5) {
          send('qr', { qr: qrLines.join('\n') })
        }
        send('done', { code })
        controller.close()
      })

      proc.on('error', (err) => {
        send('error', { message: err.message })
        controller.close()
      })

      const timeout = setTimeout(() => {
        proc.kill('SIGTERM')
      }, 5 * 60 * 1000)

      proc.on('close', () => clearTimeout(timeout))
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}
