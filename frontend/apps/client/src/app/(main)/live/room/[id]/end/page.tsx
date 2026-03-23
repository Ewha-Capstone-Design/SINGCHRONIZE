'use client';

import { Button } from '@singchronize/ui';
import { useNavigate } from '@/shared/lib/navigation';
import { cn } from '@/shared/lib/cn';
import { BuskingResultList } from '@/widgets/busking-result/ui';

import { MOCK_BUSKING_RESULT } from '@/entities/busking/model/mock';

// TODO: 실제 데이터는 useQuery로 교체
const MOCK_STREAMER_NAME = '지연';

const BuskingResultPage = () => {
  const { go, ROUTES } = useNavigate();

  return (
    <main
      className={cn(
        'relative min-h-screen',
        'bg-bg bg-no-repeat',
        'bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.15)_0%,rgba(22,22,22,0.15)_100%)]',
        'bg-size-[100%_150%] bg-position-[50%_-50%]'
      )}
    >
      <BuskingResultList streamerName={MOCK_STREAMER_NAME} items={MOCK_BUSKING_RESULT} />
      <div className='flex justify-center'>
        <Button variant={'outline'} onClick={() => go(ROUTES.live.root)}>
          홈으로 돌아가기
        </Button>
      </div>
    </main>
  );
};

export default BuskingResultPage;
