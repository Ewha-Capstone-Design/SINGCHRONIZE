'use client';

import type { TimbreDatum } from '@/entities/vocal-report';
import { ReportCard } from '@/shared/components';
import { useModal } from '@/shared/hooks';
import { VocalReportDetailModal } from '@/widgets/vocal-report/ui';

const clamp100 = (n: number) => Math.min(100, Math.max(0, n));

const TimbreBarsChart = ({ data }: { data: TimbreDatum[] }) => (
  <div className='px-8 py-10 flex flex-col gap-3'>
    {data.map((item) => {
      const v = clamp100(item.value);
      return (
        <div key={item.label} className='flex flex-col'>
          <span className='typo-14r text-gray-100'>{item.label}</span>
          <div className='grid grid-cols-[1fr_50px] items-center gap-3'>
            <div className='h-2 bg-gray-800 rounded-20 overflow-hidden'>
              <div className='h-full bg-gray-100' style={{ width: `${v}%` }} />
            </div>
            <span className='typo-18sb text-gray-100 text-right'>{v}%</span>
          </div>
        </div>
      );
    })}
  </div>
);

const TimbreBarsCard = ({
  data,
  description,
}: {
  data: TimbreDatum[];
  description?: string;
}) => {
  const { open, openModal, closeModal } = useModal();

  return (
    <>
      <ReportCard
        title='음색 분석'
        description='3가지 포인트로 목소리 성향을 짚어봐요!'
        onClick={openModal}
        className='cursor-pointer'
      >
        <TimbreBarsChart data={data} />
      </ReportCard>

      {open && (
        <VocalReportDetailModal
          title='음색 분석'
          chart={<TimbreBarsChart data={data} />}
          description={description ?? ""}
          onClose={closeModal}
        />
      )}
    </>
  );
};

export default TimbreBarsCard;
