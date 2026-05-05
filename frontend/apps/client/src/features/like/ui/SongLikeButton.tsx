'use client';

import { useModal } from '@/shared/hooks';
import { LikeIconButton } from '@/entities/song/ui';
import type { SongUiType } from '@/entities/song';
import {
  useWishlist,
  useDeleteWishlistItem,
  useAddWishlistItem,
} from '@/entities/library';
import FolderSelectModal from './FolderSelectModal';

type SongLikeButtonProps = {
  isLiked: boolean;
  songId: string;
  folderId?: string;
  song?: Pick<SongUiType, 'title' | 'artist' | 'thumbnail'>;
};

const SongLikeButton = ({ isLiked, songId, folderId, song }: SongLikeButtonProps) => {
  const { data: wishlist = [] } = useWishlist(folderId);
  const { mutate: deleteWishlistItem } = useDeleteWishlistItem();
  const { mutate: addWishlistItem } = useAddWishlistItem();
  const folderModal = useModal();

  const addToFolder = (selectedFolderId?: string) => {
    addWishlistItem({
      song_data: {
        name: song?.title ?? '',
        artist: song?.artist ?? '',
        album_image: song?.thumbnail ?? null,
        uri: songId,
      } as unknown as Record<string, never>,
      folder_id: selectedFolderId,
    });
  };

  const handleClick = () => {
    if (isLiked && folderId) {
      const item = wishlist.find((w) => w.songId === songId);
      if (item) deleteWishlistItem(item.itemId);
    } else if (!isLiked) {
      if (folderId) {
        addToFolder(folderId);
      } else {
        folderModal.openModal();
      }
    }
  };

  const handleFolderSelect = (selectedFolderId: string) => {
    addToFolder(selectedFolderId);
    folderModal.closeModal();
  };

  return (
    <>
      <LikeIconButton isLiked={isLiked} onClick={handleClick} />
      {folderModal.open && (
        <FolderSelectModal
          onSelect={handleFolderSelect}
          onClose={folderModal.closeModal}
        />
      )}
    </>
  );
};

export default SongLikeButton;
