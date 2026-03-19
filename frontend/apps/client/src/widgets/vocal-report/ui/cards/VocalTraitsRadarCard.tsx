'use client';

import {
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
} from 'recharts';
import type { RadarDatum } from '@/entities/vocal-report';
import { ReportCard } from '@/shared/components';
import { useModal } from '@/shared/hooks';
import { VocalReportDetailModal } from '@/widgets/vocal-report/ui';

type TickProps = {
  x?: number;
  y?: number;
  payload?: { value?: string };
};

const RadarAngleTick = ({ x, y, payload }: TickProps) => (
  <g transform={`translate(${x ?? 0},${y ?? 0})`}>
    <text
      x={0}
      y={0}
      dy={4}
      textAnchor='middle'
      className='typo-14r fill-(--semantic-chart-axis-strong)'
    >
      {payload?.value ?? ''}
    </text>
  </g>
);

const VocalTraitsRadarChart = ({ data }: { data: RadarDatum[] }) => (
  <ResponsiveContainer width='100%' height='100%'>
    <RadarChart data={data} outerRadius='70%'>
      <defs>
        <linearGradient id='vocalRadarFill' x1='0' y1='0' x2='0' y2='1'>
          <stop stopColor='var(--semantic-chart-primary-30)' />
          <stop offset='1' stopColor='var(--semantic-chart-primary-end)' />
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
        strokeWidth={0.7}
        dot={{ r: 3, fill: 'var(--semantic-chart-primary)' }}
      />
    </RadarChart>
  </ResponsiveContainer>
);

const VocalTraitsRadarCard = ({
  data,
  description,
}: {
  data: RadarDatum[];
  description: string;
}) => {
  const { open, openModal, closeModal } = useModal();

  return (
    <>
      <ReportCard
        title='보컬 특성'
        description='5가지 기준으로 한눈에 살펴봐요!'
        onClick={openModal}
        className='cursor-pointer'
      >
        <div className='mt-2 h-60 md:h-full'>
          <VocalTraitsRadarChart data={data} />
        </div>
      </ReportCard>

      {open && (
        <VocalReportDetailModal
          title='보컬 특성'
          chart={
            <div className='h-72'>
              <VocalTraitsRadarChart data={data} />
            </div>
          }
          description={description}
          onClose={closeModal}
        />
      )}
    </>
  );
};

export default VocalTraitsRadarCard;
