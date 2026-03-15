import crypto from 'crypto'

const SECRET_KEY = process.env.AUTH_SECRET_KEY

export function hash(text: string): string {
  return crypto
    .createHmac('sha256', SECRET_KEY)
    .update(text)
    .digest('hex')
}

export function compare(text: string, hashedText: string): boolean {
  const newHash = hash(text)
  return crypto.timingSafeEqual(
    Buffer.from(newHash, 'hex'),
    Buffer.from(hashedText, 'hex')
  )
}
