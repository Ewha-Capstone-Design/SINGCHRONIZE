export const getArchiveHistoryTitle = (dateString: string): string => {
  // "2026.01.10" or "2026-01-10" 둘 다 처리
  const normalized = dateString.trim().replace(/\./g, '-');
  const [y, m, d] = normalized.split('-').map((v) => Number(v));

  if (!y || !m || !d) return `${dateString} 추천리스트`;

  const target = new Date(y, m - 1, d);
  if (Number.isNaN(target.getTime())) return `${dateString} 추천리스트`;

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const targetDay = new Date(target.getFullYear(), target.getMonth(), target.getDate());

  const diffDays = Math.round(
    (today.getTime() - targetDay.getTime()) / (1000 * 60 * 60 * 24)
  );

  if (diffDays === 0) return '오늘 추천리스트';
  if (diffDays === 1) return '하루 전 추천리스트';
  if (diffDays === 2) return '이틀 전 추천리스트';

  return `${y}년 ${m}월 ${d}일 추천리스트`;
};
