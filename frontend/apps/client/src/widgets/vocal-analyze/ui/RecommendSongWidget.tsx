'use client';

import { cn } from '@/shared/lib/cn';
import type { RecommendSongType, RecommendTab } from '../model/types';
import RecommendPanel from './RecommendPanel';

type RecommendSongsWidgetProps = {
  situationTabs: RecommendTab<RecommendSongType>[];
  genreTabs: RecommendTab<RecommendSongType>[];
  className?: string;
};

const RecommendSongsWidget = ({
  situationTabs,
  genreTabs,
  className,
}: RecommendSongsWidgetProps) => {
  return (
    <div className={cn('grid grid-cols-1 gap-6 lg:grid-cols-2 h-186', className)}>
      <RecommendPanel
        kind='situation'
        title='상황별 추천 곡'
        description='선택한 노래 상황에 맞춘 추천이에요!'
        tabs={situationTabs}
      />

      <RecommendPanel
        kind='genre'
        title='장르별 추천 곡'
        description='선호 장르와 보컬 특성을 반영한 추천이에요!'
        tabs={genreTabs}
      />
    </div>
  );
};

export default RecommendSongsWidget;
