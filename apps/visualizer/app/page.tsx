'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Button, Card, CardBody } from '@heroui/react'
import { createClient } from '../lib/supabase/client'

export default function LandingPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const checkSession = async () => {
      const supabase = createClient()
      const {
        data: { user },
      } = await supabase.auth.getUser()
      setIsAuthenticated(!!user)
      setUserEmail(user?.email ?? null)
      setIsLoading(false)
    }
    checkSession()
  }, [])

  const handleSignOut = async () => {
    const supabase = createClient()
    await supabase.auth.signOut()
    setIsAuthenticated(false)
    setUserEmail(null)
  }

  const features = [
    {
      title: 'Mapeo 3D en tiempo real',
      description:
        'Visualiza nubes de puntos LiDAR en tiempo real directamente desde el dispositivo Raspberry Pi Pico W.',
    },
    {
      title: 'Hardware de bajo costo',
      description:
        'Arquitectura basada en microcontroladores accesibles y sensores LiDAR compactos para democratizar el mapeo 3D.',
    },
    {
      title: 'Almacenamiento en la nube',
      description:
        'Guarda y accede a tus escaneos desde cualquier lugar mediante almacenamiento en Cloudflare R2.',
    },
    {
      title: 'Interfaz interactiva',
      description:
        'Rota, amplía y explora la nube de puntos con controles intuitivos desde el navegador.',
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
      <nav className="border-b border-divider px-6 py-4 flex items-center justify-between">
        <span className="text-xl font-bold">LiDAR 3D</span>
        <div className="flex items-center gap-3">
          {!isLoading && (
            <>
              {isAuthenticated ? (
                <>
                  <div className="hidden sm:flex items-center h-8 px-3 rounded-md bg-default-100 text-xs text-default-600 max-w-[240px]">
                    <span className="truncate" title={userEmail ?? 'Sesión iniciada'}>
                      {userEmail ?? 'Sesión iniciada'}
                    </span>
                  </div>
                  <Button as={Link} href="/app" color="primary" size="sm">
                    Ir al Visualizador
                  </Button>
                  <Button
                    variant="light"
                    color="danger"
                    size="sm"
                    onClick={handleSignOut}
                  >
                    Cerrar sesión
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    as={Link}
                    href="/auth/login"
                    variant="bordered"
                    size="sm"
                  >
                    Iniciar sesión
                  </Button>
                  <Button
                    as={Link}
                    href="/auth/register"
                    color="primary"
                    size="sm"
                  >
                    Registrarse
                  </Button>
                </>
              )}
            </>
          )}
        </div>
      </nav>

      {/* Hero */}
      <section className="flex flex-col items-center text-center px-6 py-24 gap-8">
        <div className="flex flex-col gap-4 max-w-3xl">
          <h1 className="text-5xl font-bold tracking-tight">
            Mapeo 3D LiDAR de{' '}
            <span className="text-primary">bajo costo</span>
          </h1>
          <p className="text-xl text-default-500 leading-relaxed">
            Sistema de escaneo tridimensional con Raspberry Pi Pico W. Captura,
            procesa y visualiza nubes de puntos en tiempo real desde cualquier
            navegador.
          </p>
        </div>

        <div className="flex gap-4 flex-wrap justify-center">
          {!isLoading && (
            <>
              {isAuthenticated ? (
                <Button
                  as={Link}
                  href="/app"
                  color="primary"
                  size="lg"
                  className="font-semibold"
                >
                  Ir al Visualizador
                </Button>
              ) : (
                <>
                  <Button
                    as={Link}
                    href="/app"
                    color="primary"
                    size="lg"
                    className="font-semibold"
                  >
                    Ver Visualizador
                  </Button>
                  <Button
                    as={Link}
                    href="/auth/register"
                    variant="bordered"
                    size="lg"
                  >
                    Registrarse
                  </Button>
                </>
              )}
            </>
          )}
        </div>
      </section>

      {/* Features */}
      <section className="px-6 pb-24 max-w-5xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-12">
          Capacidades del sistema
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((feature) => (
            <Card key={feature.title} className="border border-divider">
              <CardBody className="px-6 py-5 flex flex-col gap-2">
                <h3 className="text-lg font-semibold">{feature.title}</h3>
                <p className="text-default-500 text-sm leading-relaxed">
                  {feature.description}
                </p>
              </CardBody>
            </Card>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-divider px-6 py-6 text-center text-default-400 text-sm">
        Sistema LiDAR 3D — Proyecto de tesis
      </footer>
    </div>
  )
}
