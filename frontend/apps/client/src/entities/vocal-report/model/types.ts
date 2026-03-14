export type RadarDatum = { label: string; value: number }; // 0~100
export type GenreDatum = { genre: string; score: number }; // 0~100
export type TimbreDatum = { label: string; value: number }; // 0~100
export type RangePoint = { note: string; score: number }; // 0~100

export type VocalReport = {
  updated_at?: string;
  traits: RadarDatum[];
  genreFit: {
    bestGenre: string;
    data: GenreDatum[];
  };
  timbre: TimbreDatum[];
  range: {
    comfort: { from: string; to: string };
    stats: { max: string; avg: string; min: string };
    data: RangePoint[];
  };
};
