'use client';

import { LikeIconButton } from '@/entities/song/ui';
import { useWishlist, useDeleteWishlistItem } from '@/entities/library';

type SongLikeButtonProps = {
  isLiked: boolean;
  songId: string;
  folderId?: string;
};

const SongLikeButton = ({ isLiked, songId, folderId }: SongLikeButtonProps) => {
  const { data: wishlist = [] } = useWishlist(folderId);
  const { mutate: deleteWishlistItem } = useDeleteWishlistItem();

  const handleClick = () => {
    if (isLiked && folderId) {
      const item = wishlist.find((w) => w.songId === songId);
      if (item) deleteWishlistItem(item.itemId);
    } else {
      // TODO: 찜하기 API 연결
      console.log('like', songId);
    }
  };

  return <LikeIconButton isLiked={isLiked} onClick={handleClick} />;
};

export default SongLikeButton;
