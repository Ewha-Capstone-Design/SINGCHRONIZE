import type { components } from '@singchronize/api';

export type GenderType = 'male' | 'female';

export type ArtistIdType = number;

export type ArtistApiType = components['schemas']['SingerInfo'];

export type ArtistUiType = {
  id: number;
  name: string;
  imageUrl: string | null;
};
