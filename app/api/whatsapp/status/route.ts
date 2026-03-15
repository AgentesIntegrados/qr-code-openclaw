import { NextResponse } from 'next/server'
import { execFile } from 'child_process'
import { promisify } from 'util'

const execFileAsync = promisify(execFile)

export async function GET() {
  try {
    const { stdout } = await execFileAsync('wacli', ['auth', 'status', '--json'], {
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
