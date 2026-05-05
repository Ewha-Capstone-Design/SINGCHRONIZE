import { useEffect, RefObject } from 'react';

const useClickOutside = (
  ref: RefObject<HTMLElement | null>,
  callback: () => void,
  enabled = true,
) => {
  useEffect(() => {
    if (!enabled) return;

    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        callback();
      }
    };

    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [ref, callback, enabled]);
};

export default useClickOutside;
