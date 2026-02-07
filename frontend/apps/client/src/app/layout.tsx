import './global.css';

const RootLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <html lang='ko'>
      <body>{children}</body>
    </html>
  );
};

export default RootLayout;
