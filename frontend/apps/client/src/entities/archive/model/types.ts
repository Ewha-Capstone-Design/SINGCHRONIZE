import type { SongApiType, SongUiType } from '@/entities/song/model/types';
import { GenreKey, SituationKey } from '@/shared/types/category';

export type ArchiveSectionAPiType = {
  rec_id: string;
  date: string;
  recording_url?: string;
  songs: SongApiType[];
};

export type ArchiveSectionUiType = {
  id: string;
  title: string;
  recordingUrl?: string;
  songs: SongUiType[];
};

export type ArchiveItemApiType = {
  id: string;
  title: string;
  artist: string;
  album_cover: string | null;
  match_rate: number;
  is_liked: boolean;
};

export type ArchiveItemUiType = {
  id: string;
  title: string;
  artist: string;
  thumbnail: string | null;
  matchRate: number;
  isLiked: boolean;
};

export type ArchiveApiType = {
  genres: GenreKey[];
  situations: SituationKey[];
  items: ArchiveItemApiType[];
};

export type ArchiveUiType = {
  genres: GenreKey[];
  situations: SituationKey[];
  items: ArchiveItemUiType[];
};
