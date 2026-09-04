import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { libraryApi } from '../api/libraryApi';
import type {
  FolderCreate,
  FolderUpdate,
  WishlistItemCreate,
  FavoriteFolderApiType,
  FavoriteSongApiType,
  HistoryItemApiType,
  ArchiveCreate,
  ArchiveUpdate,
} from '../model/types';
import { queryKeys } from '@/shared/api/queryKeys';
import { toFavoriteFolderUi, toFavoriteSongUiType, toHistoryItemUi } from './mapper';

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

// DELETE: 폴더 삭제
export const useDeleteFolder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (folderId: string) => libraryApi.deleteFolder(folderId),
    onMutate: async (folderId) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.folders });
      const previous = queryClient.getQueryData<FavoriteFolderApiType[]>(
        queryKeys.folders,
      );
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

// PATCH: 폴더 이름 변경
export const useRenameFolder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ folderId, body }: { folderId: string; body: FolderUpdate }) =>
      libraryApi.renameFolder(folderId, body),
    onMutate: async ({ folderId, body }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.folders });
      const previous = queryClient.getQueryData<FavoriteFolderApiType[]>(
        queryKeys.folders,
      );
      queryClient.setQueryData<FavoriteFolderApiType[]>(queryKeys.folders, (old = []) =>
        old.map((f) => (f.id === folderId ? { ...f, name: body.name } : f)),
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
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
    onMutate: async (body) => {
      const wishlistKey = queryKeys.wishlist(body.folder_id ?? undefined);
      await queryClient.cancelQueries({ queryKey: wishlistKey });

      const previous = queryClient.getQueryData<FavoriteSongApiType[]>(wishlistKey);

      const tempId = `temp-${crypto.randomUUID()}`;
      const tempItem: FavoriteSongApiType = {
        id: tempId,
        user_id: '',
        folder_id: body.folder_id ?? null,
        song_data: body.song_data,
        created_at: new Date().toISOString(),
        song_id: tempId,
      };

      queryClient.setQueryData<FavoriteSongApiType[]>(wishlistKey, (old = []) => [
        tempItem,
        ...old,
      ]);

      return { previous, wishlistKey };
    },
    onError: (_err, _body, context) => {
      if (context) queryClient.setQueryData(context.wishlistKey, context.previous);
    },
    onSettled: (_data, _err, body) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.wishlist(body.folder_id ?? undefined),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.folders });
    },
  });
};

// DELETE: 위시리스트 아이템 삭제
export const useDeleteWishlistItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => libraryApi.deleteWishlistItem(itemId),
    onMutate: async (itemId) => {
      await queryClient.cancelQueries({ queryKey: ['library', 'wishlist'] });

      const allCaches = queryClient.getQueriesData<FavoriteSongApiType[]>({
        queryKey: ['library', 'wishlist'],
      });

      allCaches.forEach(([key, data]) => {
        if (!data) return;
        queryClient.setQueryData<FavoriteSongApiType[]>(
          key,
          data.filter((item) => item.id !== itemId),
        );
      });

      return { allCaches };
    },
    onError: (_err, _itemId, context) => {
      context?.allCaches.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['library', 'wishlist'] });
      queryClient.invalidateQueries({ queryKey: queryKeys.folders });
    },
  });
};

// GET: 보컬 기록 조회
export const useHistory = () =>
  useQuery({
    queryKey: queryKeys.history,
    queryFn: libraryApi.getHistory,
    select: (data) => data.map(toHistoryItemUi),
  });

// POST: 보컬 기록 생성
export const useCreateHistory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ArchiveCreate) => libraryApi.createHistory(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.history }),
  });
};

// PATCH: 보컬 기록 수정
export const useUpdateHistory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ archiveId, body }: { archiveId: string; body: ArchiveUpdate }) =>
      libraryApi.updateHistory(archiveId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.history }),
  });
};

// DELETE: 보컬 기록 삭제
export const useDeleteHistory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (archiveId: string) => libraryApi.deleteHistory(archiveId),
    onMutate: async (archiveId) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.history });
      const previous = queryClient.getQueryData<HistoryItemApiType[]>(queryKeys.history);
      queryClient.setQueryData<HistoryItemApiType[]>(queryKeys.history, (old = []) =>
        old.filter((h) => h.id !== archiveId),
      );
      return { previous };
    },
    onError: (_err, _archiveId, context) => {
      queryClient.setQueryData(queryKeys.history, context?.previous);
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: queryKeys.history }),
  });
};
