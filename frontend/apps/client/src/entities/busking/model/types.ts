import type { components } from '@singchronize/api';

export type BuskingRoomApiType = components['schemas']['BuskingRoomResponse'];
export type BuskingRoomDetailApiType = components['schemas']['BuskingRoomDetailResponse'];
export type BuskingRoomCreateApiType = components['schemas']['BuskingRoomCreateResponse'];
export type BuskingRoomCreateBody = components['schemas']['BuskingRoomCreate'];
export type BuskingResultApiType = Omit<
  components['schemas']['BuskingResultResponse'],
  'reactions'
> & {
  reactions: Record<string, number>;
};
export type ThumbnailPresignedApiType =
  components['schemas']['ThumbnailPresignedResponse'];
export type LiveKitJoinApiType = components['schemas']['LiveKitJoinResponse'];
export type SetlistItemApiType = components['schemas']['SetlistItemResponse'];
export type SetlistItemCreateBody = components['schemas']['SetlistItemCreate'];

export const BUSKING_STATUS = {
  PREPARING: 'PREPARING',
  LIVE: 'LIVE',
  ENDED: 'ENDED',
} as const;

export type BuskingType = 'live' | 'record';

export type BuskingUiType = {
  id: string;
  status: BuskingType;
  thumbnail: string | null;
  nickname: string;
  profileImage: string;
  totalViewers: number;
};

export type SetlistType = {
  id: string;
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
  id: string;
  rank: number;
  title: string;
  artist: string;
  thumbnail?: string | null;
  votePercent: number;
};
