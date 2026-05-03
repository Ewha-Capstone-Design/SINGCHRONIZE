'use client';

import { useState, useEffect } from 'react';
import { IcThumbsDown, IcThumbsUp } from '@/shared/assets/icons';

type VoteType = 'match' | 'mismatch' | null;

type VotePanelProps = {
  timeLeft?: string;
  songId?: string;
  onVote?: (value: 'match' | 'mismatch') => void;
};

const VotePanel = ({ timeLeft, songId, onVote }: VotePanelProps) => {
  const [vote, setVote] = useState<VoteType>(null);

  useEffect(() => {
    setVote(null);
  }, [songId]);

  const handleVote = (type: 'match' | 'mismatch') => {
    if (type === vote || !onVote) return;
    setVote(type);
    onVote(type);
  };

  return (
    <div className='px-5 py-4 flex flex-col items-center gap-3 rounded-[14px] bg-black-80'>
      <div className='flex flex-col items-center gap-1'>
        <p className='typo-14r text-white'>노래가 어울리는지 투표해 주세요!</p>
        {timeLeft && (
          <p className='w-full text-left typo-12r text-gray-400'>
            투표 종료까지: <span className='text-accent-500'>{timeLeft}분</span>
          </p>
        )}
      </div>

      <div className='flex gap-2'>
        <button
          onClick={() => handleVote('match')}
          disabled={vote === 'match'}
          className='p-3 flex flex-col items-center gap-0.5 w-22.5 rounded-10 bg-yellow-500-30 disabled:opacity-50'
        >
          <IcThumbsUp />
          <span className='typo-12r text-brand'>어울려요</span>
        </button>
        <button
          onClick={() => handleVote('mismatch')}
          disabled={vote === 'mismatch'}
          className='p-3 flex flex-col items-center gap-0.5 w-22.5 rounded-10 bg-white-20 disabled:opacity-50'
        >
          <IcThumbsDown />
          <span className='typo-12r text-white'>안어울려요</span>
        </button>
      </div>
    </div>
  );
};

export default VotePanel;
