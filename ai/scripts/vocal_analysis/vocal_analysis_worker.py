"""
보컬 분석 워커 (프로덕션용)

DB에서 job_id를 받아서:
1. S3에서 유저 음성 다운로드
2. 보컬 분석 실행
3. 결과를 DB에 저장

현재는 스켈레톤 코드 (AWS 연결 전)
"""
import json
import tempfile
from pathlib import Path
from typing import Dict, Optional
import warnings
warnings.filterwarnings('ignore')

from user_vocal_pipeline import UserVocalPipeline


class VocalAnalysisWorker:
    """
    보컬 분석 워커
    
    프로덕션 환경에서 사용할 워커 클래스
    현재는 AWS 연결 없이 로컬 파일로 테스트 가능
    """
    
    def __init__(
        self,
        use_aws: bool = False,
        s3_bucket: Optional[str] = None,
        db_config: Optional[Dict] = None
    ):
        """
        Args:
            use_aws: AWS 사용 여부 (현재는 False)
            s3_bucket: S3 버킷 이름 (나중에 사용)
            db_config: DB 설정 (나중에 사용)
        """
        self.use_aws = use_aws
        self.s3_bucket = s3_bucket
        self.db_config = db_config
        
        # 보컬 분석 파이프라인 초기화
        self.pipeline = UserVocalPipeline()
        
        print("🎤 보컬 분석 워커 초기화 완료")
        if use_aws:
            print("  - AWS 모드: S3 + DB 연동")
        else:
            print("  - 로컬 모드: 파일 시스템 사용")
    
    def process_job(self, job_id: str, audio_path: Optional[str] = None) -> Dict:
        """
        작업 처리 메인 함수
        
        Args:
            job_id: 작업 ID
            audio_path: 로컬 테스트용 오디오 경로 (AWS 모드에서는 무시됨)
        
        Returns:
            result: 처리 결과
        """
        print("\n" + "="*70)
        print(f"📋 작업 처리 시작: job_id={job_id}")
        print("="*70)
        
        try:
            # Step 1: 오디오 파일 가져오기
            if self.use_aws:
                # TODO: S3에서 다운로드
                audio_file = self._download_from_s3(job_id)
            else:
                # 로컬 파일 사용 (테스트용)
                if audio_path is None:
                    raise ValueError("로컬 모드에서는 audio_path가 필요합니다")
                audio_file = audio_path
                print(f"\n[Step 1] 로컬 파일 사용: {audio_file}")
            
            # Step 2: 보컬 분석 실행
            print(f"\n[Step 2] 보컬 분석 실행")
            analysis_result = self.pipeline.process(
                audio_path=audio_file,
                output_dir=f"output/{job_id}",
                save_features=True
            )
            
            # Step 3: 결과 저장
            if self.use_aws:
                # TODO: DB에 저장
                self._save_to_db(job_id, analysis_result)
            else:
                # 로컬 JSON 저장 (테스트용)
                output_file = f"output/{job_id}/result.json"
                self._save_to_json(analysis_result, output_file)
                print(f"\n[Step 3] 결과 저장: {output_file}")
            
            print("\n" + "="*70)
            print(f"✅ 작업 완료: job_id={job_id}")
            print("="*70)
            
            return {
                'status': 'success',
                'job_id': job_id,
                'result': analysis_result
            }
            
        except Exception as e:
            print(f"\n❌ 작업 실패: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'status': 'failed',
                'job_id': job_id,
                'error': str(e)
            }
    
    def _download_from_s3(self, job_id: str) -> str:
        """
        S3에서 오디오 파일 다운로드
        
        TODO: 나중에 구현
        """
        print(f"\n[Step 1] S3에서 다운로드 중...")
        print(f"  - Bucket: {self.s3_bucket}")
        print(f"  - Key: users/{job_id}/audio.m4a")
        
        # TODO: boto3로 S3 다운로드
        # import boto3
        # s3 = boto3.client('s3')
        # local_path = f"/tmp/{job_id}_audio.m4a"
        # s3.download_file(
        #     Bucket=self.s3_bucket,
        #     Key=f"users/{job_id}/audio.m4a",
        #     Filename=local_path
        # )
        
        raise NotImplementedError("S3 다운로드는 아직 구현되지 않았습니다")
    
    def _save_to_db(self, job_id: str, result: Dict):
        """
        분석 결과를 DB에 저장
        
        TODO: 나중에 구현
        """
        print(f"\n[Step 3] DB에 저장 중...")
        print(f"  - job_id: {job_id}")
        
        # TODO: DB에 저장
        # import psycopg2  # PostgreSQL 예시
        # conn = psycopg2.connect(**self.db_config)
        # cursor = conn.cursor()
        # 
        # # 레이더 차트 저장
        # radar = result['report']['radar_chart']
        # cursor.execute("""
        #     UPDATE vocal_analysis_jobs
        #     SET 
        #         pitch_stability = %s,
        #         rhythm_stability = %s,
        #         dynamic_control = %s,
        #         vocal_clarity = %s,
        #         high_note_stability = %s,
        #         average_score = %s,
        #         status = 'completed',
        #         result_json = %s
        #     WHERE job_id = %s
        # """, (
        #     radar['pitch_stability'],
        #     radar['rhythm_stability'],
        #     radar['dynamic_control'],
        #     radar['vocal_clarity'],
        #     radar['high_note_stability'],
        #     radar['average'],
        #     json.dumps(result),
        #     job_id
        # ))
        # conn.commit()
        # conn.close()
        
        raise NotImplementedError("DB 저장은 아직 구현되지 않았습니다")
    
    def _save_to_json(self, result: Dict, output_file: str):
        """
        결과를 JSON 파일로 저장 (로컬 테스트용)
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # numpy array를 list로 변환
        def convert_to_serializable(obj):
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            elif hasattr(obj, 'tolist'):
                return obj.tolist()
            else:
                return obj
        
        serializable_result = convert_to_serializable(result)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, indent=2, ensure_ascii=False)
    
    def process_batch_jobs(self, jobs: list) -> list:
        """
        여러 작업을 배치로 처리
        
        Args:
            jobs: [
                {'job_id': 'job1', 'audio_path': 'path1.wav'},
                {'job_id': 'job2', 'audio_path': 'path2.wav'},
                ...
            ]
        
        Returns:
            results: 처리 결과 리스트
        """
        results = []
        
        for i, job in enumerate(jobs, 1):
            print(f"\n{'='*70}")
            print(f"배치 처리: [{i}/{len(jobs)}]")
            print(f"{'='*70}")
            
            result = self.process_job(
                job_id=job['job_id'],
                audio_path=job.get('audio_path')
            )
            results.append(result)
        
        # 배치 요약
        print("\n" + "="*70)
        print("📊 배치 처리 완료")
        print("="*70)
        success_count = sum(1 for r in results if r['status'] == 'success')
        print(f"✅ 성공: {success_count}/{len(jobs)}")
        print(f"❌ 실패: {len(jobs) - success_count}/{len(jobs)}")
        print("="*70 + "\n")
        
        return results


# ============================================================================
# 테스트용 헬퍼 함수
# ============================================================================

def test_single_job(job_id: str, audio_path: str):
    """
    단일 작업 테스트
    
    Args:
        job_id: 작업 ID
        audio_path: 오디오 파일 경로
    """
    worker = VocalAnalysisWorker(use_aws=False)
    result = worker.process_job(job_id, audio_path)
    return result


def test_batch_jobs(jobs: list):
    """
    배치 작업 테스트
    
    Args:
        jobs: [
            {'job_id': 'job1', 'audio_path': 'path1.wav'},
            {'job_id': 'job2', 'audio_path': 'path2.wav'},
        ]
    """
    worker = VocalAnalysisWorker(use_aws=False)
    results = worker.process_batch_jobs(jobs)
    return results


# ============================================================================
# CLI 실행
# ============================================================================

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description="보컬 분석 워커 (프로덕션용)"
    )
    parser.add_argument(
        "job_id",
        type=str,
        help="작업 ID"
    )
    parser.add_argument(
        "-a", "--audio",
        type=str,
        required=True,
        help="오디오 파일 경로 (로컬 테스트용)"
    )
    parser.add_argument(
        "--aws",
        action="store_true",
        help="AWS 모드 활성화 (S3 + DB)"
    )
    
    args = parser.parse_args()
    
    # 워커 실행
    try:
        worker = VocalAnalysisWorker(use_aws=args.aws)
        result = worker.process_job(args.job_id, args.audio)
        
        if result['status'] == 'success':
            print("\n✅ 처리 완료!")
            sys.exit(0)
        else:
            print(f"\n❌ 처리 실패: {result['error']}")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

