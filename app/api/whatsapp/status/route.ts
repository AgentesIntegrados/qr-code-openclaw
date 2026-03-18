import { NextResponse } from 'next/server'
import { execFile } from 'child_process'
import { promisify } from 'util'

const execFileAsync = promisify(execFile)

export async function GET() {
  // Use wacli directly — doesn't need gateway running
  try {
    const wacliPath = process.env.WACLI_PATH || 'wacli'
    const { stdout } = await execFileAsync(wacliPath, ['auth', 'status', '--json'], {
      timeout: 3000,
      killSignal: 'SIGKILL',
    })
    const result = JSON.parse(stdout)
    return NextResponse.json({
      connected: result.data?.authenticated === true,
    })
  } catch {
    return NextResponse.json({ connected: false })
  }
}
