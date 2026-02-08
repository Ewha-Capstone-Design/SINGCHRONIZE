export type SongType = {
  id: string; // uuid
  title: string; // NN
  artist: string; // NN
  album_cover?: string | null;
  tags?: unknown; // jsonb
  features?: unknown; // jsonb
  created_at?: string; // timestamptz
};
