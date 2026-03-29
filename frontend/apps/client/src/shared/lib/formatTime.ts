export const formatTime = (seconds: number) => {
  const mm = String(Math.floor(seconds / 60)).padStart(2, '0');
  const ss = String(seconds % 60).padStart(2, '0');
  return { mm, ss, formatted: `${mm}:${ss}` };
};
