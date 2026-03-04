import type { TimbreDatum } from '@/entities/vocal-report';
import { ReportCard } from '@/shared/components';

const clamp100 = (n: number) => (n < 0 ? 0 : n > 100 ? 100 : n);

const TimbreBarsCard = ({ data }: { data: TimbreDatum[] }) => {
  return (
    <ReportCard title='음색 분석' description='3가지 포인트로 목소리 성향을 짚어봐요!'>
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
    </ReportCard>
  );
};

export default TimbreBarsCard;
