import { spawn } from 'child_process'

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

      const proc = spawn('wacli', ['auth', '--idle-exit', '120s'], {
        env: { ...process.env, HOME: process.env.HOME || '/home/agents' },
      })

      let qrLines: string[] = []
      let capturing = false
      let sent = false

      function processLine(line: string) {
        // Detect QR start (line full of block chars)
        if (!capturing && /^[█▀▄▁▂▃▅▆▇░▒▓\s]{10,}$/.test(line)) {
          capturing = true
          qrLines = [line]
          return
        }

        if (capturing) {
          qrLines.push(line)
          // QR ends with a line of lower-half blocks or thin bar
          if (/^[▀▔\s─━]+$/.test(line) || (qrLines.length > 5 && line.trim() === '')) {
            send('qr', { qr: qrLines.join('\n') })
            qrLines = []
            capturing = false
            sent = true
          }
        }

        if (/linked|connected|authenticated|saved/i.test(line)) {
          send('connected', { message: line.trim() })
        }

        if (/failed|error|timeout/i.test(line) && !sent) {
          send('error', { message: line.trim() })
        }
      }

      let buffer = ''
      function onData(chunk: Buffer) {
        buffer += chunk.toString()
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.trim()) processLine(line)
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

      // Kill process if client disconnects (AbortSignal not available in start,
      // so we set a max lifetime)
      const timeout = setTimeout(() => {
        proc.kill('SIGTERM')
      }, 5 * 60 * 1000) // 5 min max

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
