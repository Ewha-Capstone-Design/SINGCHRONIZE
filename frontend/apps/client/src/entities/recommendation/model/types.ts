import type { components } from '@singchronize/api';
import type { SongApiType, FirstRecommendedSongType } from '@/entities/song/model/types';

export type RecommendationCreateBody = components['schemas']['RecommendationCreate'];

export type RecommendationFeedbackBody = components['schemas']['RecommendationFeedback'];

export type RecommendationStatusResponse = Omit<
  components['schemas']['RecommendationStatusResponse'],
  'first_recommended_songs' | 'recommended_songs'
> & {
  first_recommended_songs?: FirstRecommendedSongType[] | null;
  recommended_songs?: Record<string, SongApiType[]> | null;
};
