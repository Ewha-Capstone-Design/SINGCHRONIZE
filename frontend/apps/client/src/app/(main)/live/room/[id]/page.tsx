'use client';

import { useState } from 'react';
import { cn } from '@/shared/lib/cn';
import { IcBack } from '@/shared/assets/icons';
import { SetlistPanel, VotePanel, LiveChat } from '@/features/busking/ui';
import { BuskingSection } from '@/widgets/busking-list/ui';

import {
  MOCK_SETLIST,
  MOCK_CHAT,
  MOCK_BUSKING_LIST,
} from '@/entities/busking/model/mock';
import { MOCK_PROFILE } from '@/entities/user/model/mock';

const BuskingViewerPage = () => {
  const [showVote, setShowVote] = useState(true);

  const user = MOCK_PROFILE;

  return (
    <div
      className={cn(
        'flex h-screen',
        'bg-bg bg-no-repeat',
        'bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.15)_0%,rgba(22,22,22,0.15)_100%)]',
        'bg-size-[120%_180%] bg-position-[50%_50%]'
      )}
    >
      {/* 메인 영역 */}
      <div className='flex flex-col flex-1 overflow-y-auto scrollbar-hide'>
        {/* 헤더 */}
        <div className='px-9 flex items-center h-26 shrink-0'>
          <IcBack />

          <div className='ml-5 flex gap-2'>
            <div className='size-12 rounded-full bg-gray-600 border border-accent-600 shrink-0 overflow-hidden'>
              {user.profileImage && (
                <img
                  src={user.profileImage}
                  alt={user.nickname}
                  className='size-full object-cover'
                />
              )}
            </div>
            <div className='flex flex-col'>
              <span className='typo-16m text-white'>{user.nickname}</span>
              <span className='typo-14r text-gray-300'>30명이 같이 듣는 중</span>
            </div>
          </div>

          <div className='ml-4 px-3 py-1 flex gap-1 rounded-10 bg-accent-600 typo-16m text-white'>
            <span>LIVE</span>
            <span>·</span>
            <span>2:30</span>
          </div>
        </div>

        {/* 비디오 영역 */}
        <div className='relative ml-9 mr-5 mb-5 flex-1 min-h-120 rounded-10 overflow-hidden aspect-video'>
          <div className='size-full bg-gray-700' />

          {/* 셋리스트 오버레이 */}
          <div className='absolute top-3 left-3'>
            <SetlistPanel title='버스킹 첫 도전!' items={MOCK_SETLIST} />
          </div>

          {/* 투표 패널 */}
          {showVote && (
            <div className='absolute bottom-3 right-3'>
              <VotePanel />
            </div>
          )}
        </div>

        {/* 다른 버스킹 */}
        <div className='pt-5 pb-7 bg-gray-950'>
          <BuskingSection
            title='다른 버스킹 둘러보기'
            titleTypo='typo-20sb'
            listClassName='px-9 gap-2'
            cardVariant='sm'
            items={MOCK_BUSKING_LIST}
          />
        </div>
      </div>

      {/* 채팅 사이드바 */}
      <div className='w-96 shrink-0'>
        <LiveChat messages={MOCK_CHAT} />
      </div>
    </div>
  );
};

export default BuskingViewerPage;
