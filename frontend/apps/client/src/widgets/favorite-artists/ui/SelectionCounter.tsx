'use client';

type SelectionCounterProps = {
  maxSelect: number;
  selectedCount: number;
};

const SelectionCounter = ({ maxSelect, selectedCount }: SelectionCounterProps) => {
  return (
    <p className='typo-16r text-gray-400'>
      최대 {maxSelect}명을 선택해주세요 ({selectedCount}/{maxSelect})
    </p>
  );
};

export default SelectionCounter;
