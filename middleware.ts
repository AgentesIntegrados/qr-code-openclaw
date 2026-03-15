import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  console.log(`🔍 [${request.method}] ${request.url}`)
  console.log('📡 Headers:', Object.fromEntries(request.headers))
  
  return NextResponse.next()
}

export const config = {
  matcher: '/api/:path*',
}
