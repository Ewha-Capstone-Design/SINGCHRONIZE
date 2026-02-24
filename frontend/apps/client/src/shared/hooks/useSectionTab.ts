'use client';

import { useMemo, useState } from 'react';
import { SectionTabItem } from '../components/SectionTab';

type UseSectionTabParams = {
  items: readonly SectionTabItem[];
  initialTab?: string;
};

const useSectionTab = ({ items, initialTab }: UseSectionTabParams) => {
  const defaultTab = initialTab ?? items[0]?.key ?? '';

  const [tab, setTab] = useState<string>(defaultTab);

  const changeTab = (nextTab: string) => {
    setTab(nextTab);
  };

  const isTab = (key: string) => tab === key;

  const tabs = useMemo(() => items, [items]);

  return {
    tab,
    tabs,
    setTab,
    changeTab,
    isTab,
  };
};

export default useSectionTab;
