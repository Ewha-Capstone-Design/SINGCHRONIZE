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

type AxisTickProps = {
  x?: number;
  y?: number;
  payload?: { value?: string | number };
};

const XAxisTick = ({ x, y, payload }: AxisTickProps) => {
  const value = payload?.value ?? '';

  return (
    <g transform={`translate(${x ?? 0},${y ?? 0})`}>
      <text
        x={0}
        y={0}
        dy={16}
        textAnchor='middle'
        className='typo-14r fill-(--semantic-chart-axis-strong)'
      >
        {String(value)}
      </text>
    </g>
  );
};

const YAxisTick = ({ x, y, payload }: AxisTickProps) => {
  const value = payload?.value ?? '';

  return (
    <g transform={`translate(${x ?? 0},${y ?? 0})`}>
      <text
        x={0}
        y={0}
        dx={-8}
        dy={4}
        textAnchor='end'
        className='typo-12r fill-(--semantic-chart-axis)'
      >
        {String(value)}
      </text>
    </g>
  );
};

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
        ? 'var(--semantic-chart-primary-20)'
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
