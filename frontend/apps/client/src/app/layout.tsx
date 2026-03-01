import type { Metadata } from 'next';
import { metadataConfig } from './metadata';
import './global.css';
import { TooltipProvider } from '@singchronize/ui';
import { Sidebar } from '@/shared/components';

export const metadata: Metadata = metadataConfig;

const RootLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <html lang='ko'>
      <body>
        <TooltipProvider delayDuration={0}>
          <div className='flex min-h-screen'>
            <Sidebar />
            <main className='flex-1 bg-bg'>{children}</main>
          </div>
        </TooltipProvider>
      </body>
    </html>
  );
};

export default RootLayout;
