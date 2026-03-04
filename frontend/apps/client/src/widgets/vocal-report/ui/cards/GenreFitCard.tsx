'use client';

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import type { GenreDatum } from '@/entities/vocal-report';
import { ReportCard } from '@/shared/components';
import { XAxisTick, YAxisTick } from './AxisTicks';

type BarShapeProps = {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  payload?: { genre?: string; fill?: string };
  bestGenre: string;
};

const TopOnlyBarShape = ({ x, y, width, height, payload, bestGenre }: BarShapeProps) => {
  const _x = x ?? 0;
  const _y = y ?? 0;
  const _w = width ?? 0;
  const _h = height ?? 0;

  const isBest = payload?.genre === bestGenre;

  const fill = payload?.fill ?? 'transparent';
  const topStroke = isBest
    ? 'var(--semantic-chart-primary)'
    : 'var(--semantic-chart-muted-stroke)';

  return (
    <g>
      <rect x={_x} y={_y} width={_w} height={_h} fill={fill} />
      <line
        x1={_x}
        y1={_y}
        x2={_x + _w + 0.5}
        y2={_y}
        stroke={topStroke}
        strokeWidth={1.5}
        shapeRendering='crispEdges'
      />
    </g>
  );
};

const GenreFitCard = ({ data, bestGenre }: { data: GenreDatum[]; bestGenre: string }) => {
  const chartData = data.map((d) => ({
    ...d,
    fill:
      d.genre === bestGenre
        ? 'url(#vocalBestGenreFill)'
        : 'var(--semantic-chart-muted-fill)',
  }));

  return (
    <ReportCard title='장르 적합도' description='6가지 장르로 적합도를 비교해봐요!'>
      <div className='pt-4 flex flex-col gap-4 md:flex-row md:justify-between h-full md:items-end'>
        <p className='typo-18sb text-white whitespace-pre-line shrink-0'>
          {`지연님에게 가장 잘 맞는\n장르는 `}
          <span className='typo-18sb text-brand'>{bestGenre}</span>
          {`예요`}
        </p>

        <div className='pr-13.5 max-w-137 w-full h-55'>
          <ResponsiveContainer width='100%' height='100%'>
            <BarChart data={chartData} barCategoryGap={0} barGap={0}>
              <defs>
                <linearGradient id='vocalBestGenreFill' x1='0' y1='0' x2='0' y2='1'>
                  <stop stopColor='var(--semantic-chart-primary-30)' />
                  <stop offset='1' stopColor='var(--semantic-chart-primary-end)' />
                </linearGradient>
              </defs>

              <CartesianGrid
                strokeDasharray='3 3'
                stroke='var(--semantic-chart-grid)'
                vertical={false}
              />

              <XAxis
                dataKey='genre'
                tick={<XAxisTick />}
                axisLine={false}
                tickLine={false}
              />

              <YAxis
                domain={[0, 100]}
                tick={<YAxisTick />}
                axisLine={false}
                tickLine={false}
              />

              <Bar
                dataKey='score'
                shape={(p) => <TopOnlyBarShape {...p} bestGenre={bestGenre} />}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </ReportCard>
  );
};

export default GenreFitCard;
