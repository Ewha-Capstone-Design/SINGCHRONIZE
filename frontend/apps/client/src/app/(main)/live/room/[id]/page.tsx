'use client';

import { useState, useCallback, useEffect } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { Button } from '@singchronize/ui';
import { useModal } from '@/shared/hooks';
import { cn } from '@/shared/lib/cn';
import { useNavigate } from '@/shared/lib/navigation';
import { BackButton } from '@/shared/components';
import { BuskingSection } from '@/widgets/busking-list/ui';
import { LiveEndModal, SetlistPanel, VotePanel, LiveChat } from '@/features/busking/ui';
import { useBuskingSocket } from '@/features/busking/hooks/useBuskingSocket';
import { BuskingBadge } from '@/entities/busking/ui';

import {
  useBuskingRoom,
  useBuskingRooms,
  useEndBuskingRoom,
  useJoinBuskingRoom,
  useAdvanceSetlist,
} from '@/entities/busking';
import type { ChatMessageType } from '@/entities/busking';
import { useMe } from '@/entities/user';

const BuskingViewerPage = () => {
  const { go, ROUTES, dynamic } = useNavigate();
  const params = useParams();
  const searchParams = useSearchParams();

  const roomId = params.id as string;
  const isRecord = searchParams.get('type') === 'record';

  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [showVote] = useState(true);

  const endModal = useModal();
  const viewerEndModal = useModal();

  const { data: me } = useMe();
  const { data: room } = useBuskingRoom(roomId);
  const { data: rooms = [] } = useBuskingRooms();
  const { mutate: endRoom } = useEndBuskingRoom();
  const { mutate: joinRoom } = useJoinBuskingRoom();
  const { mutate: advanceSetlist } = useAdvanceSetlist();

  const isStreamer = !isRecord && !!me && !!room && me.id === room.host_id;

  // 시청자 입장 시 LiveKit 토큰 발급
  useEffect(() => {
    if (!isRecord && !isStreamer && roomId) joinRoom(roomId);
  }, [isRecord, isStreamer, roomId, joinRoom]);

  const handleMessage = useCallback(
    (payload: { userId: string; nickname: string; message: string }) => {
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now()}-${payload.userId}`,
          username: payload.nickname,
          message: payload.message,
        },
      ]);
    },
    [],
  );

  const { endLive, sendMessage } = useBuskingSocket({
    roomId,
    enabled: !isRecord,
    onLiveEnd: () => {
      if (!isStreamer) viewerEndModal.openModal();
    },
    onMessage: handleMessage,
  });

  // 스트리머: 종료 버튼 → LiveEndModal 오픈
  const handleEndLive = () => {
    endModal.openModal();
  };

  // 스트리머: 모달에서 확인 → 소켓 종료 후 결과 페이지
  const handleConfirmEndLive = () => {
    endLive();
    endRoom(roomId, {
      onSuccess: () => go(dynamic.liveRoomEnd(roomId, 'live')),
    });
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
        'bg-size-[120%_180%] bg-position-[50%_50%]',
      )}
    >
      {/* 메인 영역 */}
      <div className='flex flex-col flex-1 overflow-y-auto scrollbar-hide'>
        {/* 헤더 */}
        <div className='px-9 flex items-center h-26 shrink-0'>
          <BackButton />

          <div className='ml-5 flex gap-2'>
            <div className='size-12 rounded-full bg-gray-600 border border-accent-600 shrink-0 overflow-hidden'>
              {me?.profileImage && (
                <img
                  src={me.profileImage}
                  alt={me.nickname}
                  className='size-full object-cover'
                />
              )}
            </div>
            <div className='flex flex-col'>
              <span className='typo-16m text-white'>{me?.nickname}</span>
              <span className='typo-14r text-gray-300'>
                {room?.total_viewers ?? 0}명이 같이 듣는 중
              </span>
            </div>
          </div>

          <BuskingBadge
            isRecord={isRecord}
            duration={isRecord ? '3:30' : '2:30'}
            className='ml-4'
          />

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
            <SetlistPanel
              title={room?.title ?? ''}
              items={room?.setlist ?? []}
              isRecord={isRecord}
            />
          </div>

          {/* 투표 패널 */}
          {showVote && !isStreamer && (
            <div className='absolute bottom-3 right-3'>
              <VotePanel timeLeft={isRecord ? '00:07:30' : undefined} />
            </div>
          )}
        </div>

        {/* 다른 버스킹 */}
        {isStreamer ? (
          <div className='h-62 flex items-center justify-center'>
            <Button variant='normal' onClick={() => advanceSetlist(roomId)}>
              다음 곡으로
            </Button>
          </div>
        ) : (
          <div className='pt-5 pb-7 bg-gray-950'>
            <BuskingSection
              title='다른 버스킹 둘러보기'
              titleTypo='typo-20sb'
              listClassName='px-9 gap-2'
              cardVariant='sm'
              items={rooms}
            />
          </div>
        )}
      </div>

      {/* 채팅 사이드바 */}
      <div className='w-96 shrink-0'>
        <LiveChat messages={messages} onSend={sendMessage} />
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
