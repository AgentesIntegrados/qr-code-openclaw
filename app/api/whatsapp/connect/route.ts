import { spawn, execFile } from 'child_process'
import { promisify } from 'util'
import { readFile } from 'fs/promises'
import { join } from 'path'

const execFileAsync = promisify(execFile)

async function getLinkedNumber(): Promise<string | null> {
  try {
    const home = process.env.HOME || '/root'
    const credsPath = join(home, '.openclaw', 'credentials', 'whatsapp', 'default', 'creds.json')
    const creds = JSON.parse(await readFile(credsPath, 'utf-8'))
    const jid = creds?.me?.id // "5521936182339:80@s.whatsapp.net"
    if (!jid) return null
    const number = jid.split(':')[0]
    return '+' + number
  } catch {
    return null
  }
}

async function lockDmToOwner(phone: string) {
  try {
    const home = process.env.HOME || '/root'
    const cfgPath = join(home, '.openclaw', 'openclaw.json')
    const cfg = JSON.parse(await readFile(cfgPath, 'utf-8'))
    const wa = cfg.channels?.whatsapp || {}
    wa.dmPolicy = 'allowlist'
    wa.allowFrom = [phone]
    wa.groupPolicy = 'disabled'
    cfg.channels = { ...cfg.channels, whatsapp: wa }
    const { writeFile } = await import('fs/promises')
    await writeFile(cfgPath, JSON.stringify(cfg, null, 2))
    return true
  } catch {
    return false
  }
}

async function sendWelcomeMessage(phone: string) {
  try {
    await execFileAsync('openclaw', [
      'message', 'send',
      '--target', phone,
      '--message', 'Meu coração está batendo... */new* sempre que quiser iniciar um novo assunto.'
    ], {
      env: { ...process.env, HOME: process.env.HOME || '/root' },
      timeout: 30000
    })
    return true
  } catch {
    return false
  }
}

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
          send('connected', { message: 'Vinculado! Credenciais salvas com sucesso.' })

          // Post-connect: lock DM, restart gateway, send welcome
          ;(async () => {
            const phone = await getLinkedNumber()
            if (phone) {
              const locked = await lockDmToOwner(phone)
              if (locked) {
                send('log', { text: `Acesso restrito ao dono: ${phone}` })
              }
            }

            send('log', { text: 'Reiniciando gateway...' })
            try {
              await execFileAsync('openclaw', ['gateway', 'restart'], { timeout: 30000 })
              send('log', { text: 'Gateway reiniciado com sucesso!' })
              await new Promise(r => setTimeout(r, 8000))
              if (phone) {
                send('log', { text: `Enviando boas-vindas para ${phone}...` })
                const ok = await sendWelcomeMessage(phone)
                if (ok) {
                  send('log', { text: 'Mensagem de boas-vindas enviada!' })
                } else {
                  send('log', { text: 'Aviso: não foi possível enviar boas-vindas' })
                }
              }
            } catch {
              send('log', { text: 'Aviso: falha ao reiniciar gateway' })
            }
          })()
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
