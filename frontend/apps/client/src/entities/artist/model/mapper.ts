import type { ArtistApiType, ArtistUiType } from './types';

export const toArtistUi = (artist: ArtistApiType): ArtistUiType => ({
  id: artist.singer_id,
  name: artist.name,
  imageUrl: artist.photo_url ?? null,
});
