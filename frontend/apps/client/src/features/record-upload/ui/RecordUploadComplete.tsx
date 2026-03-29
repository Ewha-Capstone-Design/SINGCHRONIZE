'use client';

import { Button } from '@singchronize/ui';

type RecordUploadCompleteProps = {
  thumbnailPreview: string | null;
  onClose: () => void;
};

export const RecordUploadComplete = ({
  thumbnailPreview,
  onClose,
}: RecordUploadCompleteProps) => {
  return (
    <div className='flex flex-1 flex-col justify-center items-center'>
      <div className='flex flex-col gap-9 w-103'>
        {/* 제목 */}
        <h2 className='typo-32b text-white text-center'>
          녹음 버스킹이 업로드 되었어요!
        </h2>

        {/* 썸네일 */}
        <div className='w-full aspect-video rounded-10 overflow-hidden bg-gray-700'>
          {thumbnailPreview && (
            <img
              src={thumbnailPreview}
              alt='busking thumbnail'
              className='size-full object-cover'
            />
          )}
        </div>

        {/* 안내 문구 */}
        <ul className='self-center flex flex-col'>
          <li className='typo-16r text-gray-200 before:content-["•"] before:mr-2'>
            다른 사용자들에게 버스킹이 공개됩니다.
          </li>
          <li className='typo-16r text-gray-200 before:content-["•"] before:mr-2'>
            시청자들의 투표와 반응을 확인해보세요!
          </li>
        </ul>
      </div>

      {/* 업로드 후 모달 닫기 버튼 */}
      <Button variant={'outline'} className='mt-[6vh]' onClick={onClose}>
        홈으로 이동하기
      </Button>
    </div>
  );
};
