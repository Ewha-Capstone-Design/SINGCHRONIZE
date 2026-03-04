'use client';

import {
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
} from 'recharts';
import type { RadarDatum } from '@/entities/vocal-report';
import { InsightCard } from '@/shared/components';

type TickProps = {
  x?: number;
  y?: number;
  payload?: { value?: string };
};

const RadarAngleTick = ({ x, y, payload }: TickProps) => {
  const value = payload?.value ?? '';

  return (
    <g transform={`translate(${x ?? 0},${y ?? 0})`}>
      <text
        x={0}
        y={0}
        dy={4}
        textAnchor='middle'
        className='typo-14r fill-(--semantic-chart-axis-strong)'
      >
        {value}
      </text>
    </g>
  );
};

const VocalTraitsRadarCard = ({ data }: { data: RadarDatum[] }) => {
  return (
    <InsightCard title='보컬 특성' description='5가지 기준으로 한눈에 살펴봐요!'>
      <div className='h-60 md:h-full'>
        <ResponsiveContainer width='100%' height='120%'>
          <RadarChart data={data} outerRadius='70%'>
            <defs>
              <linearGradient id='vocalRadarFill' x1='0' y1='0' x2='0' y2='1'>
                <stop stopColor='var(--semantic-chart-primary-20)' />
              </linearGradient>
            </defs>

            <PolarGrid stroke='var(--semantic-chart-grid)' />
            <PolarAngleAxis
              dataKey='label'
              tick={<RadarAngleTick />}
              tickLine={false}
              tickSize={25}
            />

            <Radar
              dataKey='value'
              stroke='var(--semantic-chart-primary)'
              fill='url(#vocalRadarFill)'
              strokeWidth={2}
              dot={{ r: 3, fill: 'var(--semantic-chart-primary)' }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </InsightCard>
  );
};

export default VocalTraitsRadarCard;
