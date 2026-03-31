import { useEffect, useRef } from 'react';
import { useNavigate } from '@/shared/lib/navigation';
import { useLogin } from '../model/queries';

export const useKakaoLoginCallback = () => {
  const { go, ROUTES } = useNavigate();
  const { mutate: login } = useLogin();
  const hasRunRef = useRef(false);

  useEffect(() => {
    if (hasRunRef.current) return;

    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');

    if (!code) return;

    hasRunRef.current = true;

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
                go(ROUTES.home);
              }
            },
            onError: (error) => {
              console.error('로그인 실패:', error);
            },
          },
        );
      } catch (error) {
        console.error('로그인 에러:', error);
      }
    };

    processLogin();
  }, [go, ROUTES, login]);
};
