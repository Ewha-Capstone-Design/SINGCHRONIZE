'use client';

import { BuskingCarousel, BuskingSection } from '@/widgets/busking-list/ui';
import { Button } from '@singchronize/ui';
import { PageBanner } from '@/shared/components';
import { useModal } from '@/shared/hooks';
import { useNavigate } from '@/shared/lib/navigation';
import { LiveStartModal } from '@/features/busking/ui';
import { RecordUploadModal } from '@/features/record-upload';

import { useBuskingRooms } from '@/entities/busking';
import type { BuskingUiType } from '@/entities/busking';

const BuskingListPage = () => {
  const { go, dynamic } = useNavigate();
  const liveStartModal = useModal();
  const recordUploadModal = useModal();

  const { data: rooms = [] } = useBuskingRooms();

  const handleRoomClick = (item: BuskingUiType) => {
    go(dynamic.liveRoom(item.id, item.status));
  };

  return (
    <>
      <main className='flex flex-col gap-10'>
        <PageBanner
          category='온라인 버스킹'
          title='온라인 버스킹으로 노래를 들려주고, 내 목소리와 곡의 어울림을 확인해보세요!'
        />
        <BuskingCarousel items={rooms} />

        <div className='py-9 flex flex-col gap-7'>
          <div className='px-8 flex gap-3'>
            <Button onClick={liveStartModal.openModal}>라이브 버스킹 시작하기</Button>
            <Button variant='normal' onClick={recordUploadModal.openModal}>
              녹음 버스킹 올리기
            </Button>
          </div>

          <div className='flex flex-col gap-6'>
            <BuskingSection title='NOW ON AIR! 최근 업로드된 버스킹' items={rooms} onItemClick={handleRoomClick} />
            <BuskingSection title='지금 인기 있는 버스킹' items={rooms} onItemClick={handleRoomClick} />
          </div>
        </div>
      </main>

      <LiveStartModal open={liveStartModal.open} onClose={liveStartModal.closeModal} />

      <RecordUploadModal
        open={recordUploadModal.open}
        onClose={recordUploadModal.closeModal}
      />
    </>
  );
};

export default BuskingListPage;
