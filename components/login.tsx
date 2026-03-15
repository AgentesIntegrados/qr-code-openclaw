'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { MessageCircle, Lock } from 'lucide-react'
import { login, isAuthenticated } from '@/utils/auth'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const router = useRouter()

  useEffect(() => {
    if (isAuthenticated()) {
      router.push('/')
    }
  }, [router])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    try {
      const success = await login(username, password)
      if (success) {
        router.push('/')
      } else {
        setError('Usuário ou senha inválidos')
      }
    } catch (error) {
      setError('Erro ao tentar fazer login')
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-black p-4">
      <Card className="w-full max-w-md bg-zinc-950 border-zinc-900 shadow-2xl">
        <CardHeader className="border-b border-zinc-900 pb-4">
          <CardTitle className="text-2xl font-bold text-center text-zinc-100 flex items-center justify-center">
            <MessageCircle className="mr-2 text-emerald-500 h-6 w-6" />
            Login do Disparador
          </CardTitle>
        </CardHeader>
        <form onSubmit={handleLogin}>
          <CardContent className="p-6 space-y-4">
            {error && (
              <div className="text-red-500 text-sm text-center">{error}</div>
            )}
            <div className="space-y-2">
              <Label htmlFor="username" className="text-zinc-300">Usuário</Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="bg-zinc-900 border-zinc-800 text-zinc-100"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-zinc-300">Senha</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-zinc-900 border-zinc-800 text-zinc-100"
                required
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col items-center border-t border-zinc-900 pt-4 mt-2">
            <Button 
              type="submit"
              className="w-full max-w-md bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 rounded-full transition-all duration-300"
            >
              Entrar
              <Lock className="ml-2 h-4 w-4" />
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}