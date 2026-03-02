export type HistoryTagType =
  | 'AGAIN'
  | 'COMFORTABLE'
  | 'PRACTICE'
  | 'BAD_CONDITION'
  | 'NOT_MY_STYLE';

export type HistoryTagKeyType = 'all' | HistoryTagType;

type TagOption = {
  key: HistoryTagKeyType;
  label: string;
};

export const HISTORY_TAG_OPTIONS: readonly TagOption[] = [
  { key: 'all', label: '전체' },
  { key: 'AGAIN', label: '다음에 또 부를래요' },
  { key: 'COMFORTABLE', label: '부르기 편했어요' },
  { key: 'PRACTICE', label: '연습하고 싶어요' },
  { key: 'BAD_CONDITION', label: '오늘은 안 맞았어요' },
  { key: 'NOT_MY_STYLE', label: '별로예요' },
];

export const getHistoryTagLabel = (key: HistoryTagKeyType): string => {
  const found = HISTORY_TAG_OPTIONS.find((o) => o.key === key);
  return found ? found.label : key;
};

// 런타임 가드
const TAG_SET = new Set<HistoryTagType>(
  HISTORY_TAG_OPTIONS.map((o) => o.key).filter((k): k is HistoryTagType => k !== 'all')
);

export const isHistoryTag = (value: string): value is HistoryTagType =>
  TAG_SET.has(value as HistoryTagType);
