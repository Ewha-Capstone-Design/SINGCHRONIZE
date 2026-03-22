import { cn } from '@/shared/lib/cn';

type PageBannerProps = {
  category: string;
  title: string;
  className?: string;
};

const PageBanner = ({ category, title, className }: PageBannerProps) => {
  return (
    <section
      className={cn(
        'px-8 py-14 flex flex-col justify-center w-full h-56.25 bg-linear-to-b from-yellow-900/50 to-bg',
        className
      )}
    >
      <div className='flex flex-col gap-1'>
        <span className='typo-18sb text-gray-400'>{category}</span>
        <h1 className='typo-32b text-white'>{title}</h1>
      </div>
    </section>
  );
};

export default PageBanner;
