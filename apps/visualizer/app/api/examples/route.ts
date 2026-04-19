import { NextRequest, NextResponse } from 'next/server'

const ALLOWED_HOSTS = new Set([
  'pub-4fbb31ff60a64dc0a85d1af67478682f.r2.dev',
])

export async function GET(request: NextRequest) {
  const source = request.nextUrl.searchParams.get('url')

  if (!source) {
    return NextResponse.json({ error: 'Missing url parameter' }, { status: 400 })
  }

  let target: URL
  try {
    target = new URL(source)
  } catch {
    return NextResponse.json({ error: 'Invalid url parameter' }, { status: 400 })
  }

  if (target.protocol !== 'https:' || !ALLOWED_HOSTS.has(target.hostname)) {
    return NextResponse.json({ error: 'URL not allowed' }, { status: 403 })
  }

  try {
    const upstream = await fetch(target.toString(), { cache: 'no-store' })
    if (!upstream.ok) {
      return NextResponse.json(
        { error: `Upstream fetch failed (${upstream.status})` },
        { status: 502 }
      )
    }

    const payload = await upstream.json()
    return NextResponse.json(payload)
  } catch {
    return NextResponse.json({ error: 'Failed to fetch example' }, { status: 502 })
  }
}
