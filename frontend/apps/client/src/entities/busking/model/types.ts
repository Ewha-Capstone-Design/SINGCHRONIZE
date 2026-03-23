export type BuskingType = 'live' | 'record';

export type BuskingUiType = {
  id: string;
  status: BuskingType;
  thumbnail: string;
  nickname: string;
  profileImage: string;
  listenerCount: number;
};

export type SetlistType = {
  rank: number;
  title: string;
  artist: string;
  thumbnail?: string;
  isCurrent?: boolean;
};

export type ChatMessageType = {
  id: string;
  username: string;
  profileImage?: string;
  message: string;
};

export type BuskingResultItemType = {
  id: string | number;
  rank: number;
  title: string;
  artist: string;
  thumbnail?: string;
  votePercent: number;
};
