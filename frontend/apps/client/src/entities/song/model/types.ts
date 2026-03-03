export type SongApiType = {
  id: string;
  title: string;
  artist: string;
  album_cover?: string | null;
  tags?: unknown;
  features?: unknown;
  created_at?: string;
};

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
