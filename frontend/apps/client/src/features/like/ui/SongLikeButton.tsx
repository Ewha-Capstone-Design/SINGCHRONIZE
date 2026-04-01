'use client';

import { LikeIconButton } from '@/entities/song/ui';

type SongLikeButtonProps = {
  songId: string;
  isLiked: boolean;
};

const SongLikeButton = ({ songId, isLiked }: SongLikeButtonProps) => {
  const handleClick = () => {
    // TODO: 찜하기 API 연결
    console.log('like', songId);
  };

  return <LikeIconButton isLiked={isLiked} onClick={handleClick} />;
};

export default SongLikeButton;
