export type SongApiType = {
  // DB 기반 곡 데이터 구조
  id: string;
  title: string;
  artist: string;
  album_cover?: string | null;
};

export type SongDataType = {
  // Spotify 기반 곡 데이터 구조
  name: string;
  artist: string;
  album_image?: string | null;
  uri: string;
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

export type MusicSearchResultType = {
  uri: string;
  name: string;
  artist: string;
  album_image?: string | null;
};
