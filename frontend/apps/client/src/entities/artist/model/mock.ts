import type { ArtistUiType, GenderType } from '@/entities/artist/model/types';

const PICK_COUNT = 6;

const shuffle = <T>(items: readonly T[]) => {
  const pool = [...items];
  const result: T[] = [];

  while (pool.length > 0) {
    const idx = Math.floor(Math.random() * pool.length);
    const picked = pool.splice(idx, 1)[0];
    if (picked !== undefined) result.push(picked);
  }

  return result;
};

const getMockArtistsByGender = (gender: GenderType): ArtistUiType[] => {
  if (gender === 'male') {
    return [
      { id: 101, name: '박효신', imageUrl: null },
      { id: 102, name: '임영웅', imageUrl: null },
      { id: 103, name: '성시경', imageUrl: null },
      { id: 104, name: '멜로망스', imageUrl: null },
      { id: 105, name: '폴킴', imageUrl: null },
      { id: 106, name: '잔나비', imageUrl: null },
      { id: 107, name: '10CM', imageUrl: null },
      { id: 108, name: '데이식스', imageUrl: null },
      { id: 109, name: '정승환', imageUrl: null },
      { id: 110, name: '크러쉬', imageUrl: null },
    ];
  }

  return [
    { id: 201, name: '아이유', imageUrl: null },
    { id: 202, name: '태연', imageUrl: null },
    { id: 203, name: '뉴진스', imageUrl: null },
    { id: 204, name: '블랙핑크', imageUrl: null },
    { id: 205, name: '이영지', imageUrl: null },
    { id: 206, name: '한로로', imageUrl: null },
    { id: 207, name: '아이브', imageUrl: null },
    { id: 208, name: '에스파', imageUrl: null },
    { id: 209, name: '르세라핌', imageUrl: null },
    { id: 210, name: '레드벨벳', imageUrl: null },
  ];
};

// TODO: 실제 API 호출로 교체
export const fetchRecommendedArtists = async (
  gender: GenderType
): Promise<ArtistUiType[]> => {
  const shuffled = shuffle(getMockArtistsByGender(gender));
  return shuffled.slice(0, PICK_COUNT);
};
