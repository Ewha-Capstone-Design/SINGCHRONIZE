const MainLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div>
      <header>Main Layout</header>
      <main>{children}</main>
    </div>
  );
};

export default MainLayout;
