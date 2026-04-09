import type { components } from '@singchronize/api';
import type { VocalReport, RadarDatum, GenreDatum, TimbreDatum, RangePoint } from '@/entities/vocal-report';
import { formatDate } from '@/shared/lib/formatDate';

// 스키마가 Record<string, never>로 느슨하게 정의되어 있어 실제 응답 구조를 여기서 명시
type RawGenreFit = {
  bestGenre: string;
  data: GenreDatum[];
};

type RawRange = {
  comfort: { from: string; to: string };
  data: RangePoint[];
};

type VocalProfileResponse = components['schemas']['VocalProfileResponse'];

export const adaptVocalReport = (res: VocalProfileResponse): VocalReport => {
  const genreFit = res.genreFit as unknown as RawGenreFit | null;
  const range = res.range as unknown as RawRange | null;

  return {
    updated_at: res.updated_at ? formatDate(res.updated_at) : undefined,
    traits: (res.traits as unknown as RadarDatum[]) ?? [],
    genreFit: {
      bestGenre: genreFit?.bestGenre ?? '',
      data: genreFit?.data ?? [],
    },
    timbre: (res.timbre as unknown as TimbreDatum[]) ?? [],
    range: {
      comfort: {
        from: range?.comfort?.from ?? '',
        to: range?.comfort?.to ?? '',
      },
      stats: {
        max: res.observed_highest_note ?? '',
        avg: res.avg_note ?? '',
        min: res.observed_lowest_note ?? '',
      },
      data: range?.data ?? [],
    },
  };
};
