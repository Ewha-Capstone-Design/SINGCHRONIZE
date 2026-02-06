const LiveRoomPage = async ({ params }: { params: Promise<{ id: string }> }) => {
  const { id } = await params;

  return (
    <div>
      <h1>Live Room</h1>
      <p>Live ID: {id}</p>
    </div>
  );
};

export default LiveRoomPage;
