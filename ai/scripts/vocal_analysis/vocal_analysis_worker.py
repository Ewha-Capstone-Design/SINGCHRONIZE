"""
보컬 분석 워커 (프로덕션용)

흐름:
1. 입력: analysis_jobs.id (UUID) + (로컬) audio_path 또는 (AWS) s3_key
2. AWS: 행 상태 ANALYZING → S3 다운로드 → UserVocalPipeline.process() → DONE + result_data
3. 결과: 로컬은 output/<uuid>/result.json (전체), AWS는 result_data = { version, result: { report 일부 } }

Supabase analysis_jobs 스키마 (기본값):
  id, recording_id, user_id, status (vocal_analysis_status), result_data, created_at, updated_at
  status: QUEUED | UPLOADING | ANALYZING | FINDING_SONGS | DONE | FAILED

실행 예:
  로컬:  python vocal_analysis_worker.py <analysis_jobs.id> -a /path/to.wav
  AWS:   python vocal_analysis_worker.py <analysis_jobs.id> --aws --s3-key path/in/bucket.m4a
  SQS:   python vocal_analysis_worker.py --queue   # 메시지에 job_id 또는 id + s3_key

.env (다른 테이블/컬럼명일 때만):
  ANALYSIS_JOBS_TABLE=analysis_jobs
  ANALYSIS_JOBS_ID_COLUMN=id
  ANALYSIS_JOBS_TIMESTAMP_COLUMN=updated_at
  ANALYSIS_JOBS_RESULT_COLUMN=result_data
"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
import warnings
warnings.filterwarnings('ignore')

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from user_vocal_pipeline import UserVocalPipeline
from report_for_db import build_result_data_payload


# ============================================================================
# 환경 변수 로드 (ai/.env → 프로젝트 루트/.env 순서로 시도)
# recommendation_worker와 동일한 패턴
# ============================================================================
env_paths = [
    Path(__file__).parent.parent.parent / ".env",        # ai/.env
    Path(__file__).parent.parent.parent.parent / ".env", # 프로젝트 루트/.env
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ .env 파일 로드: {env_path}")
        break
else:
    load_dotenv()
    print("⚠️  .env 파일을 찾지 못했습니다. 기본 위치에서 시도합니다.")


# 보컬 분석용 SQS Queue URL (추천과 분리)
VOCAL_ANALYSIS_SQS_QUEUE_URL = os.getenv("VOCAL_ANALYSIS_SQS_QUEUE_URL")

# 유저 음성 업로드 버킷 (공통 env 사용)
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Supabase analysis_jobs — 프로젝트 기본 스키마에 맞춤 (.env 로 덮어쓰기 가능)
ANALYSIS_JOBS_TABLE = (os.getenv("ANALYSIS_JOBS_TABLE") or "analysis_jobs").strip()
ANALYSIS_JOBS_ID_COLUMN = (os.getenv("ANALYSIS_JOBS_ID_COLUMN") or "id").strip()
ANALYSIS_JOBS_TIMESTAMP_COLUMN = (os.getenv("ANALYSIS_JOBS_TIMESTAMP_COLUMN") or "updated_at").strip()
ANALYSIS_JOBS_RESULT_COLUMN = (os.getenv("ANALYSIS_JOBS_RESULT_COLUMN") or "result_data").strip()

# vocal_analysis_status enum (DB 와 동일하게 대문자)
STATUS_ANALYZING = "ANALYZING"
STATUS_DONE = "DONE"
STATUS_FAILED = "FAILED"


def _analysis_jobs_timestamp_fields() -> Dict[str, str]:
    """updated_at 등 — 컬럼명이 비어 있으면 보내지 않음."""
    if not ANALYSIS_JOBS_TIMESTAMP_COLUMN:
        return {}
    return {ANALYSIS_JOBS_TIMESTAMP_COLUMN: datetime.now(timezone.utc).isoformat()}


class VocalAnalysisWorker:
    """
    보컬 분석 워커

    - use_aws=False: audio_path(로컬 파일) → 파이프라인 → result.json
    - use_aws=True: s3_key + S3_BUCKET_NAME → 다운로드 → 파이프라인 → Supabase만
    """
    
    def __init__(
        self,
        use_aws: bool = False,
        s3_bucket: Optional[str] = None,
        db_config: Optional[Dict] = None
    ):
        """
        Args:
            use_aws: True면 S3 다운로드 + Supabase 업데이트
            s3_bucket: S3 버킷 이름 (None이면 S3_BUCKET_NAME)
            db_config: 예비 (미사용)
        """
        self.use_aws = use_aws
        self.s3_bucket = s3_bucket or S3_BUCKET
        self.db_config = db_config
        self.supabase = None
        
        # 보컬 분석 파이프라인 초기화
        self.pipeline = UserVocalPipeline()
        
        print("🎤 보컬 분석 워커 초기화 완료")
        if use_aws:
            print("  - AWS 모드: S3 + DB 연동")
            if not self.s3_bucket:
                raise RuntimeError("AWS 모드에서는 S3_BUCKET_NAME이 .env에 필요합니다.")
            # Supabase 클라이언트 초기화
            if not SUPABASE_URL or not SUPABASE_KEY:
                raise RuntimeError("AWS 모드에서는 SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY가 .env에 필요합니다.")
            from supabase import create_client
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        else:
            print("  - 로컬 모드: 파일 시스템 사용")
    
    def process_job(
        self,
        job_id: str,
        *,
        s3_key: Optional[str] = None,
        audio_path: Optional[str] = None
    ) -> Dict:
        """
        작업 처리 메인 함수
        
        Args:
            job_id: Supabase analysis_jobs.id (UUID)
            s3_key: AWS 모드에서 사용할 입력 오디오 S3 key
            audio_path: 로컬 테스트용 오디오 경로 (로컬 모드에서 사용)
        
        Returns:
            result: 처리 결과
        """
        print("\n" + "="*70)
        print(f"📋 작업 처리 시작: job_id={job_id}")
        print("="*70)
        
        temp_download_path: Optional[Path] = None
        try:
            if self.use_aws:
                try:
                    self._patch_analysis_job(job_id, {"status": STATUS_ANALYZING})
                except Exception as db_err:
                    print(f"⚠️  DB 상태 ANALYZING 반영 실패 (행 없음·RLS 등): {db_err}")

            # Step 1: 오디오 파일 가져오기
            if self.use_aws:
                if not s3_key:
                    raise ValueError("AWS 모드에서는 s3_key가 필요합니다")
                temp_download_path = self._download_from_s3(s3_key=s3_key, job_id=job_id)
                audio_file = str(temp_download_path)
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
            
            # Step 3: 결과 저장 — 로컬만 JSON 파일, AWS는 DB만
            if self.use_aws:
                self._save_to_db(job_id, analysis_result)
            else:
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

            # 실패 상태를 DB에 기록 (AWS 모드)
            if self.use_aws:
                try:
                    self._mark_job_failed(job_id, str(e))
                except Exception as db_err:
                    print(f"⚠️  실패 상태 DB 기록 중 에러: {db_err}")
            
            return {
                'status': 'failed',
                'job_id': job_id,
                'error': str(e)
            }
        finally:
            if temp_download_path:
                try:
                    temp_download_path.unlink(missing_ok=True)
                except Exception:
                    pass
    
    def _download_from_s3(self, *, s3_key: str, job_id: str) -> Path:
        """
        S3에서 오디오 파일 다운로드
        """
        print(f"\n[Step 1] S3에서 다운로드 중...")
        print(f"  - Bucket: {self.s3_bucket}")
        print(f"  - Key: {s3_key}")

        suffix = Path(s3_key).suffix or ".m4a"
        fd, tmp_path_str = tempfile.mkstemp(prefix=f"vocal_{job_id}_", suffix=suffix)
        os.close(fd)
        tmp_path = Path(tmp_path_str)

        s3 = boto3.client("s3")
        try:
            s3.download_file(self.s3_bucket, s3_key, str(tmp_path))
            print(f"✓ 다운로드 완료: {tmp_path}")
            return tmp_path
        except ClientError as e:
            tmp_path.unlink(missing_ok=True)
            err = e.response.get("Error", {}) if e.response else {}
            code = err.get("Code", "Unknown")
            msg = err.get("Message", str(e))
            raise RuntimeError(
                f"S3 download failed (bucket={self.s3_bucket}, key={s3_key}): [{code}] {msg}"
            ) from e
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise

    def _patch_analysis_job(self, row_id: str, fields: Dict) -> None:
        """analysis_jobs 한 행 업데이트 (updated_at 등 공통 필드 포함)."""
        if not self.supabase:
            raise RuntimeError("Supabase 클라이언트가 초기화되지 않았습니다.")
        payload = {**fields}
        payload.update(_analysis_jobs_timestamp_fields())
        self.supabase.table(ANALYSIS_JOBS_TABLE).update(payload).eq(
            ANALYSIS_JOBS_ID_COLUMN, row_id
        ).execute()

    def _save_to_db(self, job_id: str, result: Dict):
        """
        분석 결과를 DB(Supabase analysis_jobs)에 저장 — status=DONE, result_data=jsonb
        """
        print(f"\n[Step 3] DB에 저장 중...")
        print(f"  - {ANALYSIS_JOBS_ID_COLUMN}: {job_id}")

        # result_data: { "version", "result": { radar_chart, vocal_range, genre_fitness, timbre_profile } }
        result_data = build_result_data_payload(result)

        self._patch_analysis_job(
            job_id,
            {"status": STATUS_DONE, ANALYSIS_JOBS_RESULT_COLUMN: result_data},
        )

    def _mark_job_failed(self, job_id: str, error_message: str):
        """
        실패 시 status=FAILED, 에러는 error_message 컬럼 없음 → result_data 에 JSON 으로 저장
        """
        print(f"\n[Step 3] DB에 실패 상태 저장 중...")
        print(f"  - {ANALYSIS_JOBS_ID_COLUMN}: {job_id}")
        print(f"  - error: {error_message}")

        fail_data = {
            "error": error_message,
            "version": "v1",
        }
        self._patch_analysis_job(
            job_id,
            {"status": STATUS_FAILED, ANALYSIS_JOBS_RESULT_COLUMN: fail_data},
        )
    
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
            jobs: 로컬 — {'job_id' 또는 'id', 'audio_path'}
                  AWS — {'job_id' 또는 'id', 's3_key'}
        """
        results = []

        for i, job in enumerate(jobs, 1):
            print(f"\n{'='*70}")
            print(f"배치 처리: [{i}/{len(jobs)}]")
            print(f"{'='*70}")

            row_id = job.get("job_id") or job.get("id")
            if not row_id:
                raise ValueError("배치 job 항목에 job_id 또는 id 가 필요합니다")
            if self.use_aws:
                result = self.process_job(job_id=row_id, s3_key=job.get("s3_key"))
            else:
                result = self.process_job(job_id=row_id, audio_path=job.get("audio_path"))
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
    단일 작업 테스트 (로컬 파일)
    """
    worker = VocalAnalysisWorker(use_aws=False)
    return worker.process_job(job_id, audio_path=audio_path)


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
# SQS 연동 (추천 워커와 유사한 비동기 파이프라인)
# ============================================================================

def receive_message_from_queue(sqs_client, queue_url: str) -> Optional[Dict]:
    """
    SQS Queue에서 보컬 분석 작업 메시지 수신

    기대 메시지 형식 (JSON Body):
    {
        "job_id": "...",        # 필수 (analysis_jobs.id 와 동일 UUID)
        "id": "...",            # 위와 동일 (대체 필드)
        "s3_key": "...",        # 필수 (또는 audio_s3_key)
    }
    실패 시 메시지는 삭제하지 않음 → 재시도. 반복 실패는 SQS DLQ 설정 권장.
    """
    try:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,      # long polling
            VisibilityTimeout=300,   # 5분
        )

        messages = response.get("Messages", [])
        if not messages:
            return None

        message = messages[0]
        body = json.loads(message["Body"])

        # SNS 래핑 형식 지원
        if "Message" in body:
            body = json.loads(body["Message"])

        return {
            "receipt_handle": message["ReceiptHandle"],
            "job_id": body.get("job_id") or body.get("id"),
            "s3_key": body.get("s3_key") or body.get("audio_s3_key"),
        }
    except ClientError as e:
        print(f"⚠️  Queue 메시지 수신 실패: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️  메시지 파싱 실패: {e}")
        return None


def delete_message_from_queue(sqs_client, queue_url: str, receipt_handle: str) -> None:
    """SQS Queue에서 메시지 삭제"""
    try:
        sqs_client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle,
        )
        print("✓ Queue 메시지 삭제 완료")
    except ClientError as e:
        print(f"⚠️  Queue 메시지 삭제 실패: {e}")


def run_worker_loop():
    """
    보컬 분석 SQS 워커 메인 루프

    - VOCAL_ANALYSIS_SQS_QUEUE_URL 에서 메시지를 계속 가져와 처리
    - 실제 분석은 VocalAnalysisWorker.process_job 이 담당 (동기)이지만
      큐 기반으로 비동기 파이프라인처럼 동작
    """
    if not VOCAL_ANALYSIS_SQS_QUEUE_URL:
        raise RuntimeError("VOCAL_ANALYSIS_SQS_QUEUE_URL이 .env에 설정되지 않았습니다.")
    if not S3_BUCKET:
        raise RuntimeError("S3_BUCKET_NAME이 .env에 설정되지 않았습니다.")

    sqs_client = boto3.client("sqs")
    worker = VocalAnalysisWorker(use_aws=True)

    print("\n" + "=" * 70)
    print("🚀 보컬 분석 SQS 워커 시작")
    print("=" * 70)
    print(f"  - Queue URL: {VOCAL_ANALYSIS_SQS_QUEUE_URL}")
    print("=" * 70 + "\n")

    import time

    while True:
        try:
            message = receive_message_from_queue(sqs_client, VOCAL_ANALYSIS_SQS_QUEUE_URL)

            if not message:
                print("대기 중... (메시지 없음)")
                time.sleep(5)
                continue

            job_id = message.get("job_id")
            s3_key = message.get("s3_key")

            if not job_id or not s3_key:
                print(f"⚠️  필수 필드 누락: job_id={job_id}, s3_key={s3_key}")
                delete_message_from_queue(
                    sqs_client,
                    VOCAL_ANALYSIS_SQS_QUEUE_URL,
                    message["receipt_handle"],
                )
                continue

            print(f"\n📨 메시지 수신: job_id={job_id}")

            # 실제 보컬 분석 처리
            result = worker.process_job(job_id=job_id, s3_key=s3_key)

            if result.get("status") == "success":
                print(f"✅ 작업 완료: {job_id}")
                # 성공 시에만 삭제 (실패 시 visibility timeout 후 재시도 / DLQ 정책에 맡김)
                delete_message_from_queue(
                    sqs_client,
                    VOCAL_ANALYSIS_SQS_QUEUE_URL,
                    message["receipt_handle"],
                )
            else:
                print(
                    f"❌ 작업 실패: {job_id} ({result.get('error')}) — "
                    "메시지 유지(재전달). 필요 시 DLQ·알람을 확인하세요."
                )

        except KeyboardInterrupt:
            print("\n\n⚠️  워커 종료 요청")
            break
        except Exception as e:
            print(f"\n❌ 워커 에러: {e}")
            import traceback

            traceback.print_exc()
            time.sleep(10)


# ============================================================================
# CLI 실행
# ============================================================================

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="보컬 분석 워커 (프로덕션용, SQS/직접 실행 지원)"
    )
    parser.add_argument(
        "job_id",
        type=str,
        nargs="?",
        help="analysis_jobs.id (UUID, 직접 실행 모드)",
    )
    parser.add_argument(
        "-a",
        "--audio",
        type=str,
        help="오디오 파일 경로 (로컬 직접 실행 모드)",
    )
    parser.add_argument(
        "--s3-key",
        type=str,
        help="S3 오브젝트 키 (AWS 직접 실행 모드, --aws 와 함께 사용)",
    )
    parser.add_argument(
        "--aws",
        action="store_true",
        help="AWS 모드 (S3 다운로드 + Supabase analysis_jobs 업데이트)",
    )
    parser.add_argument(
        "--queue",
        action="store_true",
        help="SQS Queue 모드 (VOCAL_ANALYSIS_SQS_QUEUE_URL에서 메시지 소비)",
    )

    args = parser.parse_args()

    # 워커 실행
    try:
        if args.queue:
            # SQS 모드
            run_worker_loop()
        else:
            # 직접 실행 모드
            if not args.job_id:
                print("❌ 직접 실행 모드에서는 job_id가 필요합니다.")
                sys.exit(1)
            if args.aws:
                if not args.s3_key:
                    print("❌ AWS 직접 실행 모드에서는 --s3-key 가 필요합니다.")
                    sys.exit(1)
            else:
                if not args.audio:
                    print("❌ 로컬 직접 실행 모드에서는 --audio 가 필요합니다.")
                    sys.exit(1)

            worker = VocalAnalysisWorker(use_aws=args.aws)
            if args.aws:
                result = worker.process_job(args.job_id, s3_key=args.s3_key)
            else:
                result = worker.process_job(args.job_id, audio_path=args.audio)

            if result["status"] == "success":
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

