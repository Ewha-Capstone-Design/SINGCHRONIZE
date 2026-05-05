import type {
  BuskingRoomApiType,
  BuskingResultApiType,
  SetlistItemApiType,
  BuskingUiType,
  BuskingResultItemType,
  SetlistType,
  BuskingType,
} from './types';
import { BUSKING_STATUS } from './types';

const toBuskingStatus = (status: string): BuskingType =>
  status === BUSKING_STATUS.LIVE ? 'live' : 'record';

export const toBuskingUi = (room: BuskingRoomApiType): BuskingUiType => ({
  id: room.id,
  status: toBuskingStatus(room.status),
  thumbnail: room.thumbnail,
  nickname: room.host_profile?.nickname ?? '',
  profileImage: room.host_profile?.profile_img ?? '',
  totalViewers: room.total_viewers,
});

export const toSetlistUi = (
  item: SetlistItemApiType,
  currentIndex?: number,
): SetlistType => ({
  id: item.id,
  rank: item.order_index + 1,
  title: item.title,
  artist: item.artist,
  thumbnail: item.album_art_url ?? undefined,
  isCurrent: currentIndex !== undefined ? item.order_index === currentIndex : undefined,
});

export const toResultItemUi = (
  item: SetlistItemApiType,
  reactions: BuskingResultApiType['reactions'],
): BuskingResultItemType => {
  const votePercent = reactions[item.id] ?? 0;

  return {
    id: item.id,
    rank: item.order_index + 1,
    title: item.title,
    artist: item.artist,
    thumbnail: item.album_art_url ?? undefined,
    votePercent,
  };
};
