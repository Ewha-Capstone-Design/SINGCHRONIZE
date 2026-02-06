const LiveEndPage = async ({ params }: { params: Promise<{ id: string }> }) => {
  const { id } = await params;

  return (
    <div>
      <h1>Live End</h1>
      <p>Live ID: {id} 종료 리포트</p>
    </div>
  );
};
export default LiveEndPage;
