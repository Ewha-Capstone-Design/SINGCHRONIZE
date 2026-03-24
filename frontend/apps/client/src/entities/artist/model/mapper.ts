import type { ArtistApiType, ArtistUiType } from './types';

export const toArtistUi = (artist: ArtistApiType): ArtistUiType => ({
  id: artist.id,
  name: artist.name,
  imageUrl: artist.image_url ?? null,
});
