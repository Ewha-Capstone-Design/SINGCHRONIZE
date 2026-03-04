import type { VocalReport } from '@/entities/vocal-report';

type ApiResponse = {
  // TODO: 서버 스펙에 맞게 정의
};

export const adaptVocalReport = (_res: ApiResponse): VocalReport => {
  return {
    traits: [],
    genreFit: { bestGenre: '', data: [] },
    timbre: [],
    range: {
      comfort: { from: '', to: '' },
      stats: { max: '', avg: '', min: '' },
      data: [],
    },
  };
};
