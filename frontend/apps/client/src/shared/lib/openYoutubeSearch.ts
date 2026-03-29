export const openYoutubeSearch = (artist: string, title: string) => {
  const query = encodeURIComponent(`${artist} ${title}`);
  window.open(`https://www.youtube.com/results?search_query=${query}`, '_blank');
};
