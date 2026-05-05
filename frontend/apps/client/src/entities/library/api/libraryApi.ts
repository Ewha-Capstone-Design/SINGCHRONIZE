import { privateClient } from '@/shared/api/client';
import type {
  FolderCreate,
  FolderUpdate,
  WishlistItemCreate,
  ArchiveCreate,
  ArchiveUpdate,
} from '../model/types';

export const libraryApi = {
  // GET: 폴더 목록 조회
  getFolders: async () => {
    const { data, error } = await privateClient.GET('/api/v1/library/folders');
    if (error) throw error;
    return data;
  },

  // POST: 폴더 생성
  createFolder: async (body: FolderCreate) => {
    const { data, error } = await privateClient.POST('/api/v1/library/folders', { body });
    if (error) throw error;
    return data;
  },

  // PATCH: 폴더 이름 변경
  renameFolder: async (folderId: string, body: FolderUpdate) => {
    const { data, error } = await privateClient.PATCH(
      '/api/v1/library/folders/{folder_id}',
      {
        params: { path: { folder_id: folderId } },
        body,
      },
    );
    if (error) throw error;
    return data;
  },

  // DELETE: 폴더 삭제
  deleteFolder: async (folderId: string) => {
    const { error } = await privateClient.DELETE('/api/v1/library/folders/{folder_id}', {
      params: { path: { folder_id: folderId } },
    });
    if (error) throw error;
  },

  // GET: 위시리스트 조회
  getWishlist: async (folderId?: string) => {
    const { data, error } = await privateClient.GET('/api/v1/library/wishlist', {
      ...(folderId && { params: { query: { folder_id: folderId } } as any }),
    });
    if (error) throw error;
    return data;
  },

  // POST: 위시리스트 곡 추가
  addWishlistItem: async (body: WishlistItemCreate) => {
    const { data, error } = await privateClient.POST('/api/v1/library/wishlist', {
      body,
    });
    if (error) throw error;
    return data;
  },

  // DELETE: 위시리스트 곡 삭제
  deleteWishlistItem: async (itemId: string) => {
    const { error } = await privateClient.DELETE('/api/v1/library/wishlist/{item_id}', {
      params: { path: { item_id: itemId } },
    });
    if (error) throw error;
  },

  // GET: 보컬 기록 조회
  getHistory: async () => {
    const { data, error } = await privateClient.GET('/api/v1/library/history');
    if (error) throw error;
    return data;
  },

  // POST: 보컬 기록 생성
  createHistory: async (body: ArchiveCreate) => {
    const { data, error } = await privateClient.POST('/api/v1/library/history', { body });
    if (error) throw error;
    return data;
  },

  // PATCH: 보컬 기록 수정
  updateHistory: async (archiveId: string, body: ArchiveUpdate) => {
    const { data, error } = await privateClient.PATCH(
      '/api/v1/library/history/{archive_id}',
      {
        params: { path: { archive_id: archiveId } },
        body,
      },
    );
    if (error) throw error;
    return data;
  },

  // DELETE: 보컬 기록 삭제
  deleteHistory: async (archiveId: string) => {
    const { error } = await privateClient.DELETE('/api/v1/library/history/{archive_id}', {
      params: { path: { archive_id: archiveId } },
    });
    if (error) throw error;
  },
};
