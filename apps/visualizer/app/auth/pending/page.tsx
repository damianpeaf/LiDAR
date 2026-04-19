'use client'

import { useRouter } from 'next/navigation'
import { Button, Card, CardBody } from '@heroui/react'
import { createClient } from '../../../lib/supabase/client'

export default function PendingPage() {
  const router = useRouter()

  const handleSignOut = async () => {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md">
        <CardBody className="flex flex-col items-center gap-6 px-8 py-10 text-center">
          <div className="w-16 h-16 rounded-full bg-warning-100 flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-8 h-8 text-warning-600"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
              />
            </svg>
          </div>

          <div className="flex flex-col gap-2">
            <h1 className="text-2xl font-bold">Cuenta pendiente</h1>
            <p className="text-default-500 text-sm leading-relaxed">
              Tu cuenta está pendiente de aprobación. Un administrador revisará
              tu solicitud y te notificará cuando tengas acceso.
            </p>
          </div>

          <Button
            color="default"
            variant="bordered"
            onPress={handleSignOut}
            className="w-full"
          >
            Cerrar sesión
          </Button>
        </CardBody>
      </Card>
    </div>
  )
}
