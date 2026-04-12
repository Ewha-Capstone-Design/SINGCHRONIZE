'use client';

import { PageHeader } from '@/shared/components';
import { formatDate } from '@/shared/lib/formatDate';
import { BuskingCard } from '@/entities/busking/ui';

import { useMyBuskingHistory } from '@/entities/busking';
import { useMe } from '@/entities/user';

const MyBuskingPage = () => {
  const { data: me } = useMe();
  const { data } = useMyBuskingHistory();
  const history = data?.history ?? [];

  const latestDate = history[0]?.started_at ? formatDate(history[0].started_at) : null;

  return (
    <div className='py-13 flex flex-col gap-10'>
      <PageHeader
        title='나의 온라인 버스킹'
        subText={latestDate ? `최근 업데이트 ${latestDate}` : undefined}
      />
      <div className='mx-auto w-fit'>
        <div className='grid grid-cols-4 gap-x-4 gap-y-7'>
          {history.map((item) => (
            <BuskingCard
              key={item.room_id}
              variant='sm'
              item={{
                id: item.room_id,
                status:
                  item.status === 'LIVE' || item.status === 'PREPARING'
                    ? 'live'
                    : 'record',
                thumbnail: item.thumbnail ?? null,
                nickname: me?.nickname ?? '',
                profileImage: me?.profileImage ?? '',
                totalViewers: item.peak_viewer_count,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default MyBuskingPage;
