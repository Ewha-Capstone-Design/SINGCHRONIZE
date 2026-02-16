import { Button } from '@singchronize/ui';

type StartAnalysisStepProps = {
  onStart: () => void;
};

const StartAnalysisStep = ({ onStart }: StartAnalysisStepProps) => {
  return (
    <div className='flex flex-col items-center gap-16'>
      <div className='flex flex-col items-center gap-9'>
        <p className='typo-32b text-center'>이제 보컬 분석을 시작할게요!</p>
        <div className='typo-16r text-gray-200'>
          <p>잠깐!</p>
          <ul>
            <li>∙ 녹음은 최소 35초 이상 진행해 주세요</li>
            <li>∙ 1분 초과 시 자동으로 종료돼요</li>
            <li>∙ MR 없이 조용한 공간에서 녹음해 주세요</li>
            <li>∙ 다시 부르고 싶다면 뒤로가기 버튼을 눌러 주세요</li>
          </ul>
        </div>
      </div>

      <Button variant='primary' className='w-fit' onClick={onStart}>
        보컬 분석 시작하기
      </Button>
    </div>
  );
};

export default StartAnalysisStep;
