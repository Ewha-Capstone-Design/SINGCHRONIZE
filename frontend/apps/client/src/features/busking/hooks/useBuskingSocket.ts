import { useEffect, useRef, useCallback } from 'react';
import { tokenStore } from '@/shared/api/tokenStore';

type BuskingSocketEvent =
  | { type: 'LIVE_END' }
  | {
      type: 'CHAT_MESSAGE';
      payload: { userId: string; nickname: string; message: string };
    }
  | { type: 'VOTE'; payload: { songId: string; count: number } }
  | { type: 'JOIN'; payload: { userId: string; nickname: string } }
  | { type: 'LEAVE'; payload: { userId: string; nickname: string } };

interface UseBuskingSocketOptions {
  roomId: string;
  enabled?: boolean;
  onLiveEnd?: () => void;
  onMessage?: (
    payload: Extract<BuskingSocketEvent, { type: 'CHAT_MESSAGE' }>['payload']
  ) => void;
  onVote?: (payload: Extract<BuskingSocketEvent, { type: 'VOTE' }>['payload']) => void;
  onJoin?: (payload: Extract<BuskingSocketEvent, { type: 'JOIN' }>['payload']) => void;
  onLeave?: (payload: Extract<BuskingSocketEvent, { type: 'LEAVE' }>['payload']) => void;
}

export const useBuskingSocket = ({
  roomId,
  enabled = true,
  onLiveEnd,
  onMessage,
  onVote,
  onJoin,
  onLeave,
}: UseBuskingSocketOptions) => {
  const wsRef = useRef<WebSocket | null>(null);

  const onLiveEndRef = useRef(onLiveEnd);
  const onMessageRef = useRef(onMessage);
  const onVoteRef = useRef(onVote);
  const onJoinRef = useRef(onJoin);
  const onLeaveRef = useRef(onLeave);

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
    if (!enabled) return;

    const token = tokenStore.getAccess();
    const ws = new WebSocket(
      `${process.env.NEXT_PUBLIC_WS_URL}/api/v1/busking/ws/${roomId}?token=${token}`
    );
    wsRef.current = ws;

    ws.onmessage = (e) => {
      const event: BuskingSocketEvent = JSON.parse(e.data);

      switch (event.type) {
        case 'LIVE_END':
          onLiveEndRef.current?.();
          break;
        case 'CHAT_MESSAGE':
          onMessageRef.current?.(event.payload);
          break;
        case 'VOTE':
          onVoteRef.current?.(event.payload);
          break;
        case 'JOIN':
          onJoinRef.current?.(event.payload);
          break;
        case 'LEAVE':
          onLeaveRef.current?.(event.payload);
          break;
      }
    };

    ws.onerror = (e) => console.error('[BuskingSocket] error', e);

    return () => {
      ws.close();
    };
  }, [roomId, enabled]);

  const sendMessage = useCallback((message: string) => {
    wsRef.current?.send(JSON.stringify({ type: 'CHAT_MESSAGE', payload: { message } }));
  }, []);

  const endLive = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ type: 'LIVE_END' }));
  }, []);

  const sendVote = useCallback((songId: string) => {
    wsRef.current?.send(JSON.stringify({ type: 'VOTE', payload: { songId } }));
  }, []);

  return { sendMessage, endLive, sendVote };
};
