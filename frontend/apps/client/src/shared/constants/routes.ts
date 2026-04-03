// 정적 라우트
export const ROUTES = {
  login: {
    root: '/login',
    complete: '/login/complete',
    profile: '/login/profile',
    taste: '/login/taste',
  },
  home: '/home',
  recommend: {
    root: '/recommend',
    analyze: '/recommend/analyze',
    result: '/recommend/result',
  },
  live: {
    root: '/live',
    room: '/live/room',
  },
  library: '/library',
  archive: '/archive',
  my: {
    root: '/my',
    edit: '/my/edit',
    vocalReport: '/my/vocal-report',
    busking: '/my/busking',
  },
} as const;

// 동적 라우트
export const route = {
  recommendResult: (jobId: string) => `/recommend/result/${jobId}` as const,
  archiveCategory: (categoryKey: string) => `/archive/${categoryKey}` as const,
  liveRoom: (roomId: string, type?: 'live' | 'record') =>
    `/live/room/${roomId}${type ? `?type=${type}` : ''}` as const,
  liveRoomEnd: (roomId: string, type?: 'live' | 'record') =>
    `/live/room/${roomId}/end${type ? `?type=${type}` : ''}` as const,
};

// 타입 유틸리티: ROUTES 객체 내부의 모든 string 값을 Union 타입으로 추출
type LeaveValues<T> = T extends string
  ? T
  : T extends object
    ? { [K in keyof T]: LeaveValues<T[K]> }[keyof T]
    : never;

export type AppRoutePaths = LeaveValues<typeof ROUTES>;
