import type { components } from '@singchronize/api';
import type { FirstRecommendedSongType } from '@/entities/song/model/types';

export type RecommendationCreateBody = components['schemas']['RecommendationCreate'];

export type RecommendationFeedbackBody = components['schemas']['RecommendationFeedback'];

export type RecommendedSongItemType = {
  song_id: string;
  title: string;
  artist: string;
  album_cover?: string | null;
  score?: number;
};

export type RecommendationStatusResponse = Omit<
  components['schemas']['RecommendationStatusResponse'],
  'first_recommended_songs' | 'recommended_songs'
> & {
  first_recommended_songs?: FirstRecommendedSongType[] | null;
  recommended_songs?: {
    genre_recommendations?: Record<string, RecommendedSongItemType[]>;
    situation_recommendations?: Record<string, RecommendedSongItemType[]>;
  } | null;
};
