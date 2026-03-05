'use client';

import { Button } from '@singchronize/ui';
import { AudioPlayer, SectionTab } from '@/shared/components';
import { useSectionTab } from '@/shared/hooks';
import { cn } from '@/shared/lib/cn';
import { useNavigate } from '@/shared/lib/navigation';
import { VocalReportWidget } from '@/widgets/vocal-report/ui';
import { RecommendSongWidget } from '@/widgets/vocal-analyze/ui';

import { MOCK_VOCAL_REPORT } from '@/entities/vocal-report/model/mock';
import { MOCK_GENRE_TABS, MOCK_SITUATION_TABS } from '@/widgets/vocal-analyze/model/mock';

const RecommendResultPage = () => {
  const { go, ROUTES } = useNavigate();

  const { tab, tabs, changeTab } = useSectionTab({
    items: [
      { key: 'report', label: '보컬 분석' },
      { key: 'recommend', label: '추천 곡' },
    ] as const,
    initialTab: 'report',
  });

  const isReport = tab == 'report';

  // TODO: 임시 닉네임 교체 필요
  const username = '지연';

  return (
    <div
      className={cn(
        'px-9 pt-16 flex flex-1 flex-col min-h-full',
        'bg-bg bg-no-repeat transition-[background-position] duration-700 ease-out',
        'bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.15)_0%,rgba(22,22,22,0.15)_100%)] bg-size-[100%_150%] bg-position-[50%_-50%]'
      )}
    >
      <h1 className='typo-32b text-white text-center'>
        {tab == 'report'
          ? `${username}님의 보컬 분석 결과를 살펴보세요!`
          : `${username}님께 딱 맞는 곡도 만나보세요!`}
      </h1>

      <div className='mt-2 flex flex-col gap-8'>
        <div className='flex justify-between items-center'>
          <SectionTab
            items={tabs}
            value={tab}
            onChange={(nextTab) => changeTab(nextTab)}
            textClassName='typo-24b'
          />
          {isReport && <AudioPlayer src='' />}
        </div>
        {isReport ? (
          <VocalReportWidget desktopLayout='grid' report={MOCK_VOCAL_REPORT} />
        ) : (
          <RecommendSongWidget
            situationTabs={MOCK_SITUATION_TABS}
            genreTabs={MOCK_GENRE_TABS}
          />
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
