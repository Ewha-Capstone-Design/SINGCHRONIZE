import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { libraryApi } from '../api/libraryApi';
import type { FolderCreate, WishlistItemCreate, FavoriteFolderApiType } from '../model/types';
import { queryKeys } from '@/shared/api/queryKeys';
import { toFavoriteFolderUi, toFavoriteSongUiType } from './mapper';

// GET: 폴더 목록 조회
export const useFolders = () =>
  useQuery({
    queryKey: queryKeys.folders,
    queryFn: libraryApi.getFolders,
    select: (data) => data.map(toFavoriteFolderUi),
  });

// POST: 폴더 생성
export const useCreateFolder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: FolderCreate) => libraryApi.createFolder(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.folders }),
  });
};

// DELETE: 폴더 삭제 (낙관적 업데이트)
export const useDeleteFolder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (folderId: string) => libraryApi.deleteFolder(folderId),
    onMutate: async (folderId) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.folders });
      const previous = queryClient.getQueryData<FavoriteFolderApiType[]>(queryKeys.folders);
      queryClient.setQueryData<FavoriteFolderApiType[]>(queryKeys.folders, (old = []) =>
        old.filter((f) => f.id !== folderId),
      );
      return { previous };
    },
    onError: (_err, _folderId, context) => {
      queryClient.setQueryData(queryKeys.folders, context?.previous);
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: queryKeys.folders }),
  });
};

// GET: 위시리스트 조회
export const useWishlist = (folderId?: string) =>
  useQuery({
    queryKey: queryKeys.wishlist(folderId),
    queryFn: () => libraryApi.getWishlist(folderId),
    select: (data) => data.map(toFavoriteSongUiType),
  });

// POST: 위시리스트에 곡 추가
export const useAddWishlistItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: WishlistItemCreate) => libraryApi.addWishlistItem(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['library', 'wishlist'] }),
  });
};

// DELETE: 위시리스트 아이템 삭제
export const useDeleteWishlistItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => libraryApi.deleteWishlistItem(itemId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['library', 'wishlist'] }),
  });
};
