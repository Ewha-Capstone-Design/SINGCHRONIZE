'use client';

import { useParams } from 'next/navigation';
import { Button } from '@singchronize/ui';
import { useNavigate } from '@/shared/lib/navigation';
import { cn } from '@/shared/lib/cn';
import { BuskingResultList } from '@/widgets/busking-result/ui';

import { useBuskingResult } from '@/entities/busking';
import { useMe } from '@/entities/user';

const BuskingResultPage = () => {
  const { go, ROUTES } = useNavigate();
  const params = useParams();
  const roomId = params.id as string;

  const { data: me } = useMe();
  const { data: result } = useBuskingResult(roomId);

  if (!result) return null;

  return (
    <main
      className={cn(
        'relative flex flex-col min-h-screen',
        'bg-bg bg-no-repeat',
        'bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.15)_0%,rgba(22,22,22,0.15)_100%)]',
        'bg-size-[100%_150%] bg-position-[50%_-50%]',
      )}
    >
      <BuskingResultList streamerName={me?.nickname ?? ''} items={result.setlist} />
      <div className='my-auto flex justify-center items-center min-h-24'>
        <Button
          variant={'outline'}
          className='h-fit'
          onClick={() => go(ROUTES.live.root)}
        >
          홈으로 돌아가기
        </Button>
      </div>
    </main>
  );
};

export default BuskingResultPage;
