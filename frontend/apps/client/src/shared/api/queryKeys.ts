export const queryKeys = {
  me: ['me'] as const,
  blockedSingers: ['me', 'blocked-singers'] as const,
  blockedSongs: ['me', 'blocked-songs'] as const,
  searchMusic: (q: string) => ['music', 'search', q] as const,
  searchSingers: (q: string) => ['singers', 'search', q] as const,
  randomSingers: (gender: string) => ['singers', 'random', gender] as const,
};
