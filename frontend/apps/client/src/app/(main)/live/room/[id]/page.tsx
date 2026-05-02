'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { Button } from '@singchronize/ui';
import { useModal } from '@/shared/hooks';
import { cn } from '@/shared/lib/cn';
import { useNavigate } from '@/shared/lib/navigation';
import { formatElapsedDuration } from '@/shared/lib/formatTime';
import { BackButton } from '@/shared/components';
import { BuskingSection } from '@/widgets/busking-list/ui';
import {
  BuskingVideoRoom,
  HostLiveEndModal,
  ViewerLiveEndModal,
  SetlistPanel,
  VotePanel,
  LiveChat,
} from '@/features/busking/ui';
import { useBuskingSocket } from '@/features/busking/hooks/useBuskingSocket';
import { BuskingBadge } from '@/entities/busking/ui';

import {
  useBuskingRoom,
  useBuskingRooms,
  useEndBuskingRoom,
  useJoinBuskingRoom,
  useAdvanceSetlist,
  BUSKING_STATUS,
} from '@/entities/busking';
import type { ChatMessageType } from '@/entities/busking';
import { useMe } from '@/entities/user';

type LiveKitCredentials = { token: string; url: string };

const BuskingViewerPage = () => {
  const { go, ROUTES, dynamic } = useNavigate();
  const params = useParams();
  const searchParams = useSearchParams();

  const roomId = params.id as string;
  const isRecord = searchParams.get('type') === 'record';

  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [showVote] = useState(true);
  const [isLastSong, setIsLastSong] = useState(false);
  const [liveKitCredentials, setLiveKitCredentials] = useState<LiveKitCredentials | null>(null);
  const [liveDuration, setLiveDuration] = useState('00:00');
  const [viewerCount, setViewerCount] = useState(0);

  const endModal = useModal();
  const viewerEndModal = useModal();

  const { data: me } = useMe();
  const { data: room } = useBuskingRoom(roomId);
  const { data: rooms = [] } = useBuskingRooms();
  const { mutate: endRoom } = useEndBuskingRoom();
  const { mutateAsync: joinRoom } = useJoinBuskingRoom();
  const { mutate: advanceSetlist, isPending: isAdvancing } = useAdvanceSetlist();

  const isStreamer = !isRecord && !!me && !!room && me.id === room.host_id;
  const sessionEndedRef = useRef(false);

  useEffect(() => {
    if (!isRecord && room && room.status !== BUSKING_STATUS.LIVE && !sessionEndedRef.current) {
      go(ROUTES.live.root);
    }
  }, [isRecord, room, go, ROUTES.live.root]);

  useEffect(() => {
    if (isRecord || !me || !room) return;

    if (isStreamer) {
      const stored = sessionStorage.getItem(`livekit_host_${roomId}`);
      if (stored) {
        setLiveKitCredentials(JSON.parse(stored));
        sessionStorage.removeItem(`livekit_host_${roomId}`);
      }
    } else {
      joinRoom(roomId).then((data) => {
        setLiveKitCredentials({ token: data.livekit_token, url: data.livekit_url });
      });
    }
  }, [isStreamer, isRecord, roomId, me, room, joinRoom]);

  useEffect(() => {
    if (room?.total_viewers !== undefined) setViewerCount(room.total_viewers);
  }, [room?.total_viewers]);

  useEffect(() => {
    if (isRecord || !room?.started_at) return;
    const startedAt = room.started_at;
    setLiveDuration(formatElapsedDuration(startedAt));
    const id = setInterval(() => setLiveDuration(formatElapsedDuration(startedAt)), 1000);
    return () => clearInterval(id);
  }, [isRecord, room?.started_at]);

  const handleMessage = useCallback(
    (payload: { userId: string; nickname: string; message: string }) => {
      console.log('[Chat] WS 수신 CHAT_MESSAGE', payload);
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
    enabled: !isRecord && !!room && room.status === BUSKING_STATUS.LIVE,
    onLiveEnd: () => {
      sessionEndedRef.current = true;
      if (!isStreamer) viewerEndModal.openModal();
    },
    onMessage: handleMessage,
    onStateUpdate: ({ viewerCount }) => setViewerCount(viewerCount),
  });

  const handleSend = useCallback(
    (message: string) => {
      console.log('[Chat] WS 전송', message);
      sendMessage(message);
    },
    [sendMessage],
  );

  const handleAdvanceSetlist = () => {
    advanceSetlist(roomId, {
      onError: (error) => {
        const detail = (error as { detail?: { code: string } })?.detail;
        if (detail?.code === 'ALREADY_LAST_SONG') setIsLastSong(true);
      },
    });
  };

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
                {viewerCount}명이 같이 듣는 중
              </span>
            </div>
          </div>

          <BuskingBadge
            isRecord={isRecord}
            duration={liveDuration}
            className='ml-4'
          />

          {isStreamer && (
            <Button variant={'accent'} className='ml-auto' onClick={handleEndLive}>
              라이브 버스킹 종료하기
            </Button>
          )}
        </div>

        <div className='relative ml-9 mr-5 mb-5 flex-1 min-h-120 rounded-10 overflow-hidden aspect-video'>
          <div className='size-full bg-gray-700'>
            {room?.thumbnail && (
              <img src={room.thumbnail} alt={room.title} className='size-full object-cover' />
            )}
          </div>

          {/* LiveKit 오디오 연결 */}
          {!isRecord && liveKitCredentials && (
            <BuskingVideoRoom
              token={liveKitCredentials.token}
              serverUrl={liveKitCredentials.url}
              isHost={isStreamer}
            />
          )}

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
            <Button
              variant='normal'
              onClick={handleAdvanceSetlist}
              disabled={isAdvancing || isLastSong}
            >
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
        <LiveChat messages={messages} onSend={handleSend} />
      </div>

      {/* 스트리머: 종료 확인 모달 */}
      {endModal.open && (
        <HostLiveEndModal onClose={endModal.closeModal} onConfirm={handleConfirmEndLive} />
      )}

      {viewerEndModal.open && (
        <ViewerLiveEndModal onConfirm={handleConfirmViewerEnd} />
      )}
    </div>
  );
};

export default BuskingViewerPage;
