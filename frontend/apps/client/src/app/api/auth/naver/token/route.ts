import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { code, redirect_uri, state } = await req.json();

  const params = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: process.env.NEXT_PUBLIC_NAVER_CLIENT_ID ?? '',
    client_secret: process.env.NAVER_CLIENT_SECRET ?? '',
    redirect_uri,
    code,
    state,
  });

  const response = await fetch(`https://nid.naver.com/oauth2.0/token?${params.toString()}`, {
    method: 'GET',
  });

  const data = await response.json();

  if (!response.ok || data.error) {
    return NextResponse.json({ error: data.error_description ?? '토큰 발급 실패' }, { status: 400 });
  }

  return NextResponse.json({ access_token: data.access_token });
}
