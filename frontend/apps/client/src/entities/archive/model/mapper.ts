import { toSongUi } from '@/entities/song/model/mapper';
import type { ArchiveSectionAPiType, ArchiveSectionUiType } from './types';
import type { ArchiveItemApiType, ArchiveItemUiType } from './types';
import type { ArchiveApiType, ArchiveUiType } from './types';
import { getArchiveHistoryTitle } from './utils';

export const toArchiveSectionUi = (raw: ArchiveSectionAPiType): ArchiveSectionUiType => ({
  id: raw.rec_id,
  title: getArchiveHistoryTitle(raw.date),
  recordingUrl: raw.recording_url,
  songs: raw.songs.map(toSongUi),
});

export const toArchiveItemUi = (item: ArchiveItemApiType): ArchiveItemUiType => {
  return {
    id: item.id,
    title: item.title,
    artist: item.artist,
    thumbnail: item.album_cover,
    matchRate: item.match_rate,
    isLiked: item.is_liked,
  };
};

export const toArchiveUi = (data: ArchiveApiType): ArchiveUiType => {
  return {
    genres: data.genres,
    situations: data.situations,
    items: data.items.map(toArchiveItemUi),
  };
};
