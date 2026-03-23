'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { Button } from '@singchronize/ui';
import { useModal } from '@/shared/hooks';
import { cn } from '@/shared/lib/cn';
import { IcBack } from '@/shared/assets/icons';
import { BuskingSection } from '@/widgets/busking-list/ui';
import { LiveEndModal, SetlistPanel, VotePanel, LiveChat } from '@/features/busking/ui';

import { useNavigate } from '@/shared/lib/navigation';
import { useBuskingSocket } from '@/features/busking/hooks/useBuskingSocket';

import {
  MOCK_SETLIST,
  MOCK_CHAT,
  MOCK_BUSKING_LIST,
} from '@/entities/busking/model/mock';
import { MOCK_PROFILE } from '@/entities/user/model/mock';

const MOCK_ROLE = 'viewer' as 'viewer' | 'streamer';

const BuskingViewerPage = () => {
  const { go, back, ROUTES, dynamic } = useNavigate();
  const params = useParams();
  const roomId = params.roomId as string;

  const [showVote, setShowVote] = useState(true);

  const endModal = useModal();
  const viewerEndModal = useModal();

  const user = MOCK_PROFILE;
  const isStreamer = MOCK_ROLE === 'streamer';

  const { endLive } = useBuskingSocket({
    roomId,
    onLiveEnd: () => {
      if (!isStreamer) viewerEndModal.openModal();
    },
  });

  // 스트리머: 종료 버튼 → LiveEndModal 오픈
  const handleEndLive = () => {
    endModal.openModal();
  };

  // 스트리머: 모달에서 확인 → 소켓 종료 후 결과 페이지
  const handleConfirmEndLive = () => {
    // endLive(); // TODO: 웹소켓 기능 구현 시 주석 해제
    go(dynamic.liveRoomEnd(roomId));
  };

  // 시청자: 방송 종료 알림 모달에서 확인
  const handleConfirmViewerEnd = () => {
    viewerEndModal.closeModal();
    go(ROUTES.live.root);
  };

  return (
    <div
      className={cn(
        'flex h-screen',
        'bg-bg bg-no-repeat',
        'bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.20)_0%,rgba(22,22,22,0.20)_100%)]',
        'bg-size-[120%_180%] bg-position-[50%_50%]'
      )}
    >
      {/* 메인 영역 */}
      <div className='flex flex-col flex-1 overflow-y-auto scrollbar-hide'>
        {/* 헤더 */}
        <div className='px-9 flex items-center h-26 shrink-0'>
          <IcBack onClick={back} />

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

          {isStreamer && (
            <Button variant={'accent'} className='ml-auto' onClick={handleEndLive}>
              라이브 버스킹 종료하기
            </Button>
          )}
        </div>

        {/* 비디오 영역 */}
        <div className='relative ml-9 mr-5 mb-5 flex-1 min-h-120 rounded-10 overflow-hidden aspect-video'>
          <div className='size-full bg-gray-700' />

          {/* 셋리스트 오버레이 */}
          <div className='absolute top-3 left-3'>
            <SetlistPanel title='버스킹 첫 도전!' items={MOCK_SETLIST} />
          </div>

          {/* 투표 패널 */}
          {showVote && !isStreamer && (
            <div className='absolute bottom-3 right-3'>
              <VotePanel />
            </div>
          )}
        </div>

        {/* 다른 버스킹 */}
        {isStreamer ? (
          <div className='h-62'></div> // 셋리스트 넘기기 버튼
        ) : (
          <div className='pt-5 pb-7 bg-gray-950'>
            <BuskingSection
              title='다른 버스킹 둘러보기'
              titleTypo='typo-20sb'
              listClassName='px-9 gap-2'
              cardVariant='sm'
              items={MOCK_BUSKING_LIST}
            />
          </div>
        )}
      </div>

      {/* 채팅 사이드바 */}
      <div className='w-96 shrink-0'>
        <LiveChat messages={MOCK_CHAT} />
      </div>

      {/* 스트리머: 종료 확인 모달 */}
      {endModal.open && (
        <LiveEndModal onClose={endModal.closeModal} onConfirm={handleConfirmEndLive} />
      )}

      {/* 시청자: 방송 종료 알림 모달 */}
      {viewerEndModal.open && (
        <div className='absolute inset-0 flex items-center justify-center bg-dim z-20'>
          <div className='p-8 flex flex-col items-center gap-6 w-80 rounded-10 bg-gray-800'>
            <p className='typo-18sb text-white text-center'>라이브가 종료되었습니다</p>
            <Button variant={'accent'} className='w-52' onClick={handleConfirmViewerEnd}>
              확인
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default BuskingViewerPage;
