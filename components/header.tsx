'use client'

import { useRouter } from 'next/navigation'
import { Button } from "@/components/ui/button"
import { LogOut, UserPlus } from 'lucide-react'
import { logout } from '@/utils/auth'
import { BrazilFlag } from './flags'

export default function Header() {
  const router = useRouter()

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  const handleNewNumber = () => {
    router.push('/connect')
  }

  return (
    <div className="fixed top-0 right-0 p-4 z-50 flex items-center gap-2">
      <Button
        onClick={handleNewNumber}
        variant="ghost"
        className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50"
      >
        <UserPlus className="h-4 w-4 mr-2" />
        Cadastrar novo número
      </Button>
      <div className="px-2">
        <BrazilFlag />
      </div>
      <Button
        onClick={handleLogout}
        variant="ghost"
        className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50"
      >
        <LogOut className="h-4 w-4 mr-2" />
        Sair
      </Button>
    </div>
  )
}
