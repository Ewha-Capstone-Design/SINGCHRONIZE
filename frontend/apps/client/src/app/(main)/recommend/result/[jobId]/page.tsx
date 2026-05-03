'use client';

import { useParams } from 'next/navigation';
import { Button } from '@singchronize/ui';
import { AudioPlayer, SectionTab } from '@/shared/components';
import { useSectionTab } from '@/shared/hooks';
import { cn } from '@/shared/lib/cn';
import { useNavigate } from '@/shared/lib/navigation';
import { VocalReportWidget } from '@/widgets/vocal-report/ui';
import { RecommendSongWidget } from '@/widgets/vocal-analyze/ui';
import { useRecordedAudio, useRecommendResult } from '@/features/recommend/model';

import { useVocalProfile } from '@/entities/analysis';
import { useMe } from '@/entities/user';

const SECTION_TABS = [
  { key: 'report', label: '보컬 분석' },
  { key: 'recommend', label: '추천 곡' },
] as const;

const RecommendResultPage = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const { go, ROUTES } = useNavigate();

  const audioSrc = useRecordedAudio(jobId);
  const { isLoading, situationTabs, genreTabs } = useRecommendResult(jobId);

  const { data: report } = useVocalProfile();
  const { data: me } = useMe();
  const username = me?.nickname ?? '사용자';

  const { tab, tabs, changeTab } = useSectionTab({
    items: SECTION_TABS,
    initialTab: 'report',
  });

  const isReport = tab === 'report';

  return (
    <div
      className={cn(
        'px-9 pt-16 flex flex-1 flex-col min-h-full',
        'bg-bg bg-no-repeat transition-[background-position] duration-700 ease-out',
        'bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.15)_0%,rgba(22,22,22,0.15)_100%)] bg-size-[100%_150%] bg-position-[50%_-50%]',
      )}
    >
      <h1 className='typo-32b text-white text-center'>
        {isReport
          ? `${username}님의 보컬 분석 결과를 살펴보세요!`
          : `${username}님께 딱 맞는 곡도 만나보세요!`}
      </h1>

      <div className='mt-2 flex flex-col gap-8'>
        <div className='flex justify-between items-center'>
          <SectionTab
            items={tabs}
            value={tab}
            onChange={changeTab}
            textClassName='typo-24b'
          />
          {isReport && <AudioPlayer src={audioSrc} />}
        </div>

        {isReport ? (
          report && <VocalReportWidget desktopLayout='grid' report={report} />
        ) : isLoading ? (
          <div className='flex items-center justify-center h-186 typo-20r text-gray-500'>
            추천 곡을 준비하고 있어요...
          </div>
        ) : (
          <RecommendSongWidget situationTabs={situationTabs} genreTabs={genreTabs} />
        )}
      </div>

      <div className='flex flex-1 items-center justify-center gap-3 min-h-20'>
        <Button variant={'outline'} onClick={() => go(ROUTES.home)}>
          홈으로 돌아가기
        </Button>
        <Button variant={'normal'} onClick={() => go(ROUTES.live.root)}>
          추천 곡 불러보기
        </Button>
      </div>
    </div>
  );
};

export default RecommendResultPage;
