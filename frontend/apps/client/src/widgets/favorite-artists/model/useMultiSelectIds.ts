'use client';

import { useCallback, useEffect, useState } from 'react';
import type { ArtistIdType } from '@/entities/artist/model/types';

type Params = {
  initialSelectedIds?: ArtistIdType[];
  maxSelect?: number;
};

export const useMultiSelectIds = ({ initialSelectedIds, maxSelect }: Params) => {
  const [selectedIds, setSelectedIds] = useState<ArtistIdType[]>(
    initialSelectedIds ?? []
  );

  useEffect(() => {
    setSelectedIds(initialSelectedIds ?? []);
  }, [initialSelectedIds]);

  const toggle = useCallback(
    (id: ArtistIdType) => {
      setSelectedIds((prev) => {
        const exists = prev.includes(id);
        if (exists) return prev.filter((x) => x !== id);

        return [...prev, id];
      });
    },
    [maxSelect]
  );

  const clear = useCallback(() => {
    setSelectedIds([]);
  }, []);

  return { selectedIds, setSelectedIds, toggle, clear };
};
