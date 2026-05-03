'use client';

import { LiveKitRoom, RoomAudioRenderer } from '@livekit/components-react';

interface BuskingVideoRoomProps {
  token: string;
  serverUrl: string;
  isHost: boolean;
}

const BuskingVideoRoom = ({ token, serverUrl, isHost }: BuskingVideoRoomProps) => (
  <LiveKitRoom
    token={token}
    serverUrl={serverUrl}
    audio={isHost}
    video={false}
    className='hidden'
  >
    <RoomAudioRenderer />
  </LiveKitRoom>
);

export default BuskingVideoRoom;
