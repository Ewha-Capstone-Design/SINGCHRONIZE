import { useEffect } from 'react';
import { useNavigate } from '@/shared/lib/navigation';
import { useLogin } from '../model/queries';

let isProcessing = false;

export const useNaverLoginCallback = () => {
  const { go, ROUTES } = useNavigate();
  const { mutate: login } = useLogin();

  useEffect(() => {
    if (isProcessing) return;

    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');

    if (!code || !state) return;

    const savedState = localStorage.getItem('naver_oauth_state');
    if (state !== savedState) {
      console.error('Naver OAuth state 불일치');
      go(ROUTES.login.root);
      return;
    }
    localStorage.removeItem('naver_oauth_state');

    isProcessing = true;

    const getNaverToken = async (authCode: string, oauthState: string) => {
      const response = await fetch('/api/auth/naver/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: authCode,
          redirect_uri: process.env.NEXT_PUBLIC_NAVER_REDIRECT_URI || '',
          state: oauthState,
        }),
      });

      if (!response.ok) {
        throw new Error('네이버 토큰 발급에 실패했습니다.');
      }

      return response.json();
    };

    const processLogin = async () => {
      try {
        const { access_token } = await getNaverToken(code, state);

        login(
          {
            provider: 'naver',
            credential: access_token,
          },
          {
            onSuccess: (data) => {
              window.history.replaceState({}, '', window.location.pathname);
              if (data.is_new_user) {
                go(ROUTES.login.profile);
              } else {
                const next = localStorage.getItem('login_next');
                localStorage.removeItem('login_next');
                go(next ?? ROUTES.home);
              }
            },
            onError: (error) => {
              console.error('로그인 실패:', error);
              isProcessing = false;
              go(ROUTES.login.root);
            },
          },
        );
      } catch (error) {
        console.error('로그인 에러:', error);
        isProcessing = false;
        go(ROUTES.login.root);
      }
    };

    processLogin();
  }, [go, ROUTES, login]);
};
