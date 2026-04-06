// 카카오 로그인
export const loginWithKakao = (): void => {
  const clientId = process.env.NEXT_PUBLIC_KAKAO_JS_KEY;
  const redirectUri = process.env.NEXT_PUBLIC_KAKAO_REDIRECT_URI;

  if (!clientId) {
    throw new Error('NEXT_PUBLIC_KAKAO_JS_KEY가 설정되지 않았습니다.');
  }

  if (!redirectUri) {
    throw new Error('NEXT_PUBLIC_KAKAO_REDIRECT_URI가 설정되지 않았습니다.');
  }

  const next = new URLSearchParams(window.location.search).get('next');
  if (next) localStorage.setItem('login_next', next);

  const state = crypto.randomUUID();
  localStorage.setItem('kakao_oauth_state', state);

  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: 'code',
    state,
  });

  window.location.href = `https://kauth.kakao.com/oauth/authorize?${params.toString()}`;
};

// 네이버 로그인
export const loginWithNaver = async (): Promise<string> => {
  throw new Error('Naver 로그인이 아직 구현되지 않았습니다.');
};
