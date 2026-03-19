export const getEulReul = (word: string): string => {
  const lastChar = word.at(-1);
  if (!lastChar) return '을';
  const code = lastChar.charCodeAt(0);
  if (code < 0xac00 || code > 0xd7a3) return '을';
  return (code - 0xac00) % 28 > 0 ? '을' : '를';
};
