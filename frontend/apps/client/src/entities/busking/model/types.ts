export type BuskingType = 'live' | 'record';

export type BuskingUiType = {
  id: string;
  status: BuskingType;
  thumbnail: string;
  nickname: string;
  listenerCount: number;
  profileImage: string;
};
