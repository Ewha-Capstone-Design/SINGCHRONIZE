import createClient from 'openapi-fetch';
import type { paths as _paths } from '@singchronize/api';
import { tokenStore } from './tokenStore';

type PatchQuery<Q> = Q extends object
  ? Omit<Q, 'args' | 'kwargs'> & { args?: unknown; kwargs?: unknown }
  : Q;

type PatchParams<P> = P extends object
  ? Omit<P, 'query'> & { query?: PatchQuery<P extends { query: infer Q } ? Q : never> }
  : P;

type PatchMethod<M> = M extends object
  ? {
      [K in keyof M]: K extends 'parameters' ? PatchParams<M[K]> | undefined : M[K];
    }
  : M;

type PatchPathItem<PI> = PI extends object ? { [K in keyof PI]: PatchMethod<PI[K]> } : PI;

type paths = { [P in keyof _paths]: PatchPathItem<_paths[P]> };

export const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3000';

export const publicClient = createClient<paths>({ baseUrl: BASE_URL });

export const privateClient = createClient<paths>({ baseUrl: BASE_URL });

privateClient.use({
  onRequest({ request }) {
    const token = tokenStore.getAccess();
    if (token) request.headers.set('Authorization', `Bearer ${token}`);
    return request;
  },

  async onResponse({ response, request }) {
    if (response.status !== 401) return response;

    const refreshToken = tokenStore.getRefresh();
    if (!refreshToken) return response;

    const { data, error } = await publicClient.POST('/api/v1/auth/refresh', {
      headers: { Authorization: `Bearer ${refreshToken}` },
    });

    if (error) {
      tokenStore.clear();
      return response;
    }

    tokenStore.setAccess(data.access_token);
    tokenStore.setRefresh(data.refresh_token);

    const retryHeaders = new Headers(request.headers);
    retryHeaders.set('Authorization', `Bearer ${data.access_token}`);
    return fetch(new Request(request, { headers: retryHeaders }));
  },
});
