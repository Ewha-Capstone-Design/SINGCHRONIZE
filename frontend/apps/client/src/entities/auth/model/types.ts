import type { components } from '@singchronize/api';

export type AuthProvider = 'kakao' | 'naver';

export type LoginResponse = components['schemas']['LoginResponse'];
export type TokenResponse = components['schemas']['TokenResponse'];
export type SocialLoginRequest = components['schemas']['SocialLoginRequest'];
export type WithdrawRequest = components['schemas']['WithdrawRequest'];
