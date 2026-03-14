import type { VocalReport } from '@/entities/vocal-report';

export const MOCK_VOCAL_REPORT: VocalReport = {
  updated_at: '2026.02.03',
  traits: [
    { label: '음정 안정성', value: 85 },
    { label: '발성 수준', value: 60 },
    { label: '리듬 안정성', value: 25 },
    { label: '호흡 안정성', value: 90 },
    { label: '소리 밀도', value: 40 },
  ],
  genreFit: {
    bestGenre: '발라드',
    data: [
      { genre: '발라드', score: 100 },
      { genre: '댄스', score: 50 },
      { genre: 'POP', score: 65 },
      { genre: '트로트', score: 15 },
      { genre: '락·메탈', score: 92 },
      { genre: 'R&B', score: 75 },
    ],
  },
  timbre: [
    { label: '밝기', value: 72 },
    { label: '따뜻함', value: 60 },
    { label: '풍부함', value: 90 },
  ],
  range: {
    comfort: { from: 'G3', to: 'E4' },
    stats: { max: 'G5', avg: 'A4', min: 'C3' },
    data: [
      { note: 'C3', score: 55 },
      { note: 'E3', score: 65 },
      { note: 'G3', score: 74 },
      { note: 'C4', score: 82 },
      { note: 'E4', score: 86 },
      { note: 'G4', score: 70 },
      { note: 'C5', score: 50 },
      { note: 'E5', score: 25 },
    ],
  },
};
