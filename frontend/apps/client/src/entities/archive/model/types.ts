import type { components, paths } from '@singchronize/api';
import type { SongUiType } from '@/entities/song/model/types';

export type ArchiveSongApiType = components['schemas']['ArchiveSong'];
export type ArchiveRecItemApiType = components['schemas']['ArchiveRecItem'];
export type ArchiveDateGroupApiType = components['schemas']['ArchiveDateGroup'];
export type RecommendationArchiveApiType =
  components['schemas']['RecommendationArchiveResponse'];
export type RecommendationArchiveParams = NonNullable<
  paths['/api/v1/library/history/recommendations']['get']['parameters']['query']
>;

export type ArchiveSectionUiType = {
  id: string;
  title: string;
  recordingUrl?: string;
  songs: SongUiType[];
};

export type ArchiveItemUiType = {
  id: string;
  title: string;
  artist: string;
  thumbnail: string | null;
  matchRate: number;
  isLiked: boolean;
};
