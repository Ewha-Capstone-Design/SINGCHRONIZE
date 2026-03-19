import { PageHeader } from '@/shared/components';
import { BuskingCard } from '@/entities/busking/ui';

import { MOCK_BUSKING_LIST } from '@/entities/busking/model/mock';

const MyBuskingPage = () => {
  return (
    <div className='py-13 flex flex-col gap-10'>
      <PageHeader title='나의 온라인 버스킹' subText={`최근 업데이트 2026.02.03`} />
      <div className='mx-auto w-fit'>
        <div className='grid grid-cols-4 gap-x-4 gap-y-7'>
          {MOCK_BUSKING_LIST.map((busking) => (
            <BuskingCard key={busking.id} variant='sm' busking={busking} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default MyBuskingPage;
