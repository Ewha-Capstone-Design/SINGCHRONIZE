'use client';

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import type { RangePoint } from '@/entities/vocal-report';
import { ReportCard } from '@/shared/components';
import { cn } from '@/shared/lib/cn';
import { XAxisTick, YAxisTick } from './AxisTicks';

const StatPill = ({ label, value }: { label: string; value: string }) => {
  return (
    <div
      className={cn(
        'py-4 flex justify-center items-center gap-2 w-37.5 rounded-20',
        'border border-gray-700 text-center'
      )}
    >
      <div className='w-11 typo-14r text-gray-300'>{label}</div>
      <div className='w-11 typo-20sb text-gray-100'>{value}</div>
    </div>
  );
};

const RangeAnalysisCard = ({
  data,
  comfort,
  stats,
}: {
  data: RangePoint[];
  comfort: { from: string; to: string };
  stats: { max: string; avg: string; min: string };
}) => {
  return (
    <ReportCard title='음역대 분석' description='가장 편한 음역을 확인해봐요!'>
      <div className='pt-4 flex flex-col gap-4 md:flex-row md:justify-between h-full md:items-end'>
        <p className='typo-18sb text-white whitespace-pre-line shrink-0'>
          {`지연님에게 가장 편안한\n음역대는 `}
          <span className='typo-18sb text-brand'>
            {comfort.from}-{comfort.to}
          </span>
          {`예요`}
        </p>

        <div className='pr-13.5 flex flex-col md:flex-row gap-9 w-full'>
          <div className='w-full h-60'>
            <ResponsiveContainer width='100%' height='100%'>
              <AreaChart data={data} margin={{ left: 0, right: 10, top: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id='vocalRangeFill' x1='0' y1='0' x2='0' y2='1'>
                    <stop stopColor='var(--semantic-chart-primary-30)' />
                    <stop offset='1' stopColor='var(--semantic-chart-primary-end)' />
                  </linearGradient>
                </defs>

                <CartesianGrid
                  strokeDasharray='3 3'
                  stroke='var(--semantic-chart-grid)'
                />
                <XAxis dataKey='note' tick={<XAxisTick />} />
                <YAxis domain={[0, 100]} tick={<YAxisTick />} />

                <ReferenceLine
                  x={comfort.from}
                  stroke='var(--semantic-chart-primary)'
                  strokeOpacity={0.7}
                  strokeDasharray='4 4'
                />
                <ReferenceLine
                  x={comfort.to}
                  stroke='var(--semantic-chart-primary)'
                  strokeOpacity={0.7}
                  strokeDasharray='4 4'
                />

                <Area
                  type='monotone'
                  dataKey='score'
                  stroke='var(--semantic-chart-primary)'
                  fill='url(#vocalRangeFill)'
                  strokeWidth={1}
                  dot={{ r: 3, fill: 'var(--semantic-chart-primary)' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className='flex flex-row md:flex-col gap-4'>
            <StatPill label='최고음' value={stats.max} />
            <StatPill label='평균음' value={stats.avg} />
            <StatPill label='최저음' value={stats.min} />
          </div>
        </div>
      </div>
    </ReportCard>
  );
};

export default RangeAnalysisCard;
