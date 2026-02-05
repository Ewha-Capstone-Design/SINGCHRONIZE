export default function Home() {
  return (
    <main className='p-10 bg-base text-white text- min-h-screen'>
      {/* Head */}
      <section>
        <h1 className='text-38b text-brand'>Head 38B</h1>
        <h2 className='text-32b'>Head 32B</h2>
      </section>

      {/* Body */}
      <section>
        <p className='text-20sb'>Body 20 SemiBold</p>
        <p className='text-20r'>Body 20 Regular</p>
        <p className='text-18sb'>Body 18 SemiBold</p>
        <p className='text-16r text-gray-300'>Body 16 Regular</p>
      </section>

      {/* Colors */}
      <section className='space-x-4'>
        <span className='text-brand'>Brand Color</span>
        <span className='text-accent'>Accent Color</span>
      </section>

      {/* Radius */}
      <section className='flex gap-4'>
        <div className='w-24 h-24 bg-brand rounded-10' />
        <div className='w-24 h-24 bg-brand rounded-20' />
      </section>

      {/* Dim */}
      <section className='relative h-32'>
        <div className='absolute inset-0 bg-dim flex items-center justify-center'>
          <span className='text-20sb'>Dim Layer</span>
        </div>
      </section>
    </main>
  );
}
