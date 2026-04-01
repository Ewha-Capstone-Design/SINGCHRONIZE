import type { components } from '@singchronize/api';

export type SongApiType = components['schemas']['ArchiveSongInfo'];

export type SongUiType = {
  id: string | number;
  title: string;
  artist: string;
  thumbnail?: string;
  isLiked?: boolean;
};

export type RankedSongType = SongUiType & {
  rank: number;
  likeCount?: number;
  isLiked?: boolean;
};

export type MatchedSongType = SongUiType & {
  matchRate: number;
  isLiked?: boolean;
};
