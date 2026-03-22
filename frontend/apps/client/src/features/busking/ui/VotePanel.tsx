'use client';

import { IcThumbsDown, IcThumbsUp } from '@/shared/assets/icons';
import { useState } from 'react';

type VoteType = 'up' | 'down' | null;

const VotePanel = () => {
  const [vote, setVote] = useState<VoteType>(null);

  return (
    <div className='px-5 py-4 flex flex-col items-center gap-3 rounded-[14px] bg-black-80'>
      <p className='typo-14r text-white'>노래가 어울리는지 투표해 주세요!</p>
      <div className='flex gap-2'>
        <button
          onClick={() => setVote('up')}
          className={`p-3 flex flex-col items-center gap-0.5 w-22 rounded-10 bg-yellow-500-30`}
        >
          <IcThumbsUp />
          <span className='typo-12r text-brand'>어울려요</span>
        </button>
        <button
          onClick={() => setVote('down')}
          className={`p-3 flex flex-col items-center gap-0.5 w-22 rounded-10 bg-white-20`}
        >
          <IcThumbsDown />
          <span className='typo-12r text-white'>안어울려요</span>
        </button>
      </div>
    </div>
  );
};

export default VotePanel;
