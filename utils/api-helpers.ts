interface FetchWithRetryOptions extends RequestInit {
  retries?: number
  delayMs?: number
}

export async function fetchWithRetry(
  url: string, 
  options: FetchWithRetryOptions = {}
) {
  const { retries = 3, delayMs = 1000, ...fetchOptions } = options

  for (let i = 0; i < retries; i++) {
    try {
      console.log(`🔄 Tentativa ${i + 1} de ${retries} para ${url}`)
      
      const response = await fetch(url, fetchOptions)
      
      if (response.ok) {
        console.log(`✅ Requisição bem sucedida para ${url}`)
        return response
      }
      
      console.log(`⚠️ Tentativa ${i + 1} falhou com status ${response.status}`)
      
      if (i < retries - 1) {
        const delay = delayMs * (i + 1)
        console.log(`⏳ Aguardando ${delay}ms antes da próxima tentativa...`)
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    } catch (error) {
      console.error(`❌ Erro na tentativa ${i + 1}:`, error)
      
      if (i === retries - 1) throw error
      
      const delay = delayMs * (i + 1)
      console.log(`⏳ Aguardando ${delay}ms antes da próxima tentativa...`)
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  throw new Error(`Máximo de ${retries} tentativas excedido para ${url}`)
}

export function handleApiError(error: unknown): string {
  if (error instanceof Error) return error.message
  if (typeof error === 'string') return error
  return 'Erro desconhecido na requisição'
}

export function createApiResponse<T>(data: T, success = true, status = 200) {
  return Response.json({
    success,
    payload: data
  }, { status })
}

export function createApiErrorResponse(error: unknown, status = 500) {
  return Response.json({
    success: false,
    error: handleApiError(error)
  }, { status }) 