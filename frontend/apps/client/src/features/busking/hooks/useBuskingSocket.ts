import { useEffect, useRef, useCallback } from 'react';
import { tokenStore } from '@/shared/api/tokenStore';

type BuskingSocketEvent =
  | { type: 'live_end' }
  | { type: 'session_ended' }
  | { type: 'chat'; user_id: string; nickname: string; profile_img?: string | null; message: string }
  | { type: 'new_chat'; payload: { userId: string; nickname: string; profileImg?: string | null; message: string } }
  | { type: 'vote'; payload: { songId: string; count: number } }
  | { type: 'join'; payload: { userId: string; nickname: string } }
  | { type: 'leave'; payload: { userId: string; nickname: string } }
  | { type: 'state_update'; current_song_index: number; viewer_count: number };

type ChatPayload = { userId: string; nickname: string; profileImg?: string | null; message: string };

interface UseBuskingSocketOptions {
  roomId: string;
  enabled?: boolean;
  onLiveEnd?: () => void;
  onMessage?: (payload: ChatPayload) => void;
  onVote?: (payload: { songId: string; count: number }) => void;
  onJoin?: (payload: { userId: string; nickname: string }) => void;
  onLeave?: (payload: { userId: string; nickname: string }) => void;
  onStateUpdate?: (payload: { currentSongIndex: number; viewerCount: number }) => void;
}

const MAX_RECONNECT_DELAY_MS = 30_000;

export const useBuskingSocket = ({
  roomId,
  enabled = true,
  onLiveEnd,
  onMessage,
  onVote,
  onJoin,
  onLeave,
  onStateUpdate,
}: UseBuskingSocketOptions) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectDelayRef = useRef(1000);

  const onLiveEndRef = useRef(onLiveEnd);
  const onMessageRef = useRef(onMessage);
  const onVoteRef = useRef(onVote);
  const onJoinRef = useRef(onJoin);
  const onLeaveRef = useRef(onLeave);
  const onStateUpdateRef = useRef(onStateUpdate);

  useEffect(() => {
    onLiveEndRef.current = onLiveEnd;
  }, [onLiveEnd]);
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);
  useEffect(() => {
    onVoteRef.current = onVote;
  }, [onVote]);
  useEffect(() => {
    onJoinRef.current = onJoin;
  }, [onJoin]);
  useEffect(() => {
    onLeaveRef.current = onLeave;
  }, [onLeave]);
  useEffect(() => {
    onStateUpdateRef.current = onStateUpdate;
  }, [onStateUpdate]);

  useEffect(() => {
    if (!enabled) return;

    let isMounted = true;

    const connect = () => {
      if (!isMounted) return;

      const token = tokenStore.getAccess();
      const ws = new WebSocket(
        `${process.env.NEXT_PUBLIC_WS_URL}/api/v1/busking/ws/${roomId}?token=${token}`,
      );
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectDelayRef.current = 1000;
      };

      ws.onmessage = (e) => {
        console.log('[WS 수신]', e.data);
        const event: BuskingSocketEvent = JSON.parse(e.data);

        switch (event.type) {
          case 'live_end':
          case 'session_ended':
            onLiveEndRef.current?.();
            break;
          case 'chat':
            onMessageRef.current?.({
              userId: event.user_id,
              nickname: event.nickname,
              profileImg: event.profile_img,
              message: event.message,
            });
            break;
          case 'new_chat':
            onMessageRef.current?.(event.payload);
            break;
          case 'vote':
            onVoteRef.current?.(event.payload);
            break;
          case 'join':
            onJoinRef.current?.(event.payload);
            break;
          case 'leave':
            onLeaveRef.current?.(event.payload);
            break;
          case 'state_update':
            onStateUpdateRef.current?.({
              currentSongIndex: event.current_song_index,
              viewerCount: event.viewer_count,
            });
            break;
        }
      };

      ws.onerror = () => {};

      ws.onclose = () => {
        if (!isMounted) return;
        const delay = reconnectDelayRef.current;
        reconnectDelayRef.current = Math.min(delay * 2, MAX_RECONNECT_DELAY_MS);
        reconnectTimerRef.current = setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      wsRef.current?.close();
    };
  }, [roomId, enabled]);

  const send = useCallback((data: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const sendMessage = useCallback(
    (message: string) => send({ type: 'chat', message }),
    [send],
  );

  const endLive = useCallback(() => send({ type: 'live_end' }), [send]);

  const sendVote = useCallback(
    (songId: string) => send({ type: 'vote', payload: { songId } }),
    [send],
  );

  return { sendMessage, endLive, sendVote };
};
