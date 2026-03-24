export type GenderType = 'male' | 'female';

export type ArtistIdType = number;

export type ArtistApiType = {
  id: number;
  name: string;
  image_url: string | null;
};

export type ArtistUiType = {
  id: number;
  name: string;
  imageUrl: string | null;
};
