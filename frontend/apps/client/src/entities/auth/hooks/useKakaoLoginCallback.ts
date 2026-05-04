import { useEffect } from 'react';
import { useNavigate } from '@/shared/lib/navigation';
import { useLogin } from '../model/queries';

let isProcessing = false;

export const useKakaoLoginCallback = () => {
  const { go, ROUTES } = useNavigate();
  const { mutate: login } = useLogin();

  useEffect(() => {
    if (isProcessing) return;

    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');

    if (!code || !state) return;

    const savedState = localStorage.getItem('kakao_oauth_state');
    if (state !== savedState) {
      console.error('Kakao OAuth state 불일치');
      go(ROUTES.login.root);
      return;
    }
    localStorage.removeItem('kakao_oauth_state');

    isProcessing = true;

    const getKakaoToken = async (authCode: string) => {
      const response = await fetch('https://kauth.kakao.com/oauth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        },
        body: new URLSearchParams({
          grant_type: 'authorization_code',
          client_id: process.env.NEXT_PUBLIC_KAKAO_JS_KEY || '',
          redirect_uri: process.env.NEXT_PUBLIC_KAKAO_REDIRECT_URI || '',
          code: authCode,
        }),
      });

      if (!response.ok) {
        throw new Error('카카오 토큰 발급에 실패했습니다.');
      }

      return response.json();
    };

    const processLogin = async () => {
      try {
        const { access_token } = await getKakaoToken(code);

        login(
          {
            provider: 'kakao',
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
