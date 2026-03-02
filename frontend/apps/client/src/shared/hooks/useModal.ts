'use client';

import { useCallback, useState } from 'react';

const useModal = (initialOpen = false) => {
  const [open, setOpen] = useState(initialOpen);

  const openModal = useCallback(() => setOpen(true), []);
  const closeModal = useCallback(() => setOpen(false), []);
  const toggleModal = useCallback(() => setOpen((v) => !v), []);

  return { open, setOpen, openModal, closeModal, toggleModal };
};

export default useModal;
