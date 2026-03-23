'use client';

import { Button, InputField } from '@singchronize/ui';
import { ThumbnailUploader } from './ThumbnailUploader';

type LiveStartStep1Props = {
  title: string;
  thumbnailPreview: string | null;
  onTitleChange: (value: string) => void;
  onThumbnailChange: (file: File, preview: string) => void;
  onNext: () => void;
};

export const LiveStartStep1 = ({
  title,
  thumbnailPreview,
  onTitleChange,
  onThumbnailChange,
  onNext,
}: LiveStartStep1Props) => {
  const canGoNext = title.trim().length > 0;

  return (
    <div className='flex flex-col'>
      <section className='flex flex-col gap-4'>
        <h2 className='typo-28b text-white'>라이브 버스킹 제목</h2>
        <InputField
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder='제목을 입력해주세요'
        />
      </section>

      <section className='mt-11 flex flex-col gap-4'>
        <h2 className='typo-28b text-white'>라이브 버스킹 썸네일</h2>
        <ThumbnailUploader preview={thumbnailPreview} onChange={onThumbnailChange} />
        <ul className='ml-2 typo-16r text-gray-200'>
          <li>∙ 내 버스킹을 돋보이게 할 썸네일을 설정해 보세요.</li>
          <li>∙ 설정하지 않으면 프로필 사진이 기본 화면으로 표시됩니다.</li>
        </ul>
      </section>

      <Button onClick={onNext} disabled={!canGoNext} className='mx-auto mt-12'>
        다음으로
      </Button>
    </div>
  );
};
