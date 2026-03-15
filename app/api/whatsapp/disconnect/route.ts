import { NextResponse } from 'next/server'
import { execFile } from 'child_process'
import { promisify } from 'util'

const execFileAsync = promisify(execFile)
const wacliPath = process.env.WACLI_PATH || 'wacli'
const wacliStore = process.env.WACLI_STORE || ''

export async function POST() {
  try {
    await execFileAsync(wacliPath, ['auth', 'logout'], {
      timeout: 15000,
      env: {
        ...process.env,
        ...(wacliStore ? { WACLI_STORE: wacliStore } : {}),
      },
    })
    return NextResponse.json({ success: true })
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    )
  }
}
