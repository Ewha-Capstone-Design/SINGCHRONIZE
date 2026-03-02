import type { Metadata } from 'next';
import { metadataConfig } from './metadata';
import './global.css';
import { TooltipProvider } from '@singchronize/ui';

export const metadata: Metadata = metadataConfig;

const RootLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <html lang='ko'>
      <body className='h-screen overflow-hidden bg-bg'>
        <TooltipProvider delayDuration={0}>{children}</TooltipProvider>
      </body>
    </html>
  );
};

export default RootLayout;
