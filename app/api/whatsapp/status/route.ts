import { NextResponse } from 'next/server'
import { execFile } from 'child_process'
import { promisify } from 'util'

const execFileAsync = promisify(execFile)

export async function GET() {
  try {
    const { stdout } = await execFileAsync('openclaw', ['channels', 'status', '--json'], {
      timeout: 10000,
    })
    const result = JSON.parse(stdout)
    // Check if whatsapp channel is linked/connected
    const wa = result?.channels?.find?.((c: any) => c.channel === 'whatsapp') || result
    const connected = wa?.linked === true || wa?.connected === true || wa?.data?.authenticated === true
    return NextResponse.json({ connected })
  } catch {
    // Fallback: try wacli directly
    try {
      const wacliPath = process.env.WACLI_PATH || 'wacli'
      const { stdout } = await execFileAsync(wacliPath, ['auth', 'status', '--json'], {
        timeout: 10000,
      })
      const result = JSON.parse(stdout)
      return NextResponse.json({
        connected: result.data?.authenticated === true,
      })
    } catch {
      return NextResponse.json({ connected: false })
    }
  }
}
