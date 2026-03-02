export const nextSelectedWithAll = <T extends string>(
  prev: ReadonlySet<T | 'all'>,
  key: T | 'all'
): Set<T | 'all'> => {
  const next = new Set(prev);

  if (key === 'all') {
    return new Set(['all']);
  }

  if (next.has('all')) next.delete('all');

  if (next.has(key)) next.delete(key);
  else next.add(key);

  if (next.size === 0) next.add('all');

  return next;
};
