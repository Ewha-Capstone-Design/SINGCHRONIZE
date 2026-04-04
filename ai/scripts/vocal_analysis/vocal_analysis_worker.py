"""
보컬 분석 워커 (프로덕션용)

흐름:
1. 입력: analysis_jobs.id (UUID) + (로컬) audio_path 또는 (AWS) s3_key
2. AWS: 행 상태 ANALYZING → S3 다운로드 → UserVocalPipeline.process() → DONE + result_data
   (기본: 화면용 result만 저장, 필요 시 env로 scoring_song_aligned 포함 가능)
3. 결과: 로컬은 output/<uuid>/result.json, AWS는 analysis_jobs DONE 저장 후 user_vocal_profiles UPSERT

Supabase analysis_jobs 스키마 (기본값):
  id, recording_id, user_id, status (vocal_analysis_status), result_data, created_at, updated_at
  status: QUEUED | UPLOADING | ANALYZING | FINDING_SONGS | DONE | FAILED

실행 예 (반드시 이 디렉터리에서 실행 — import 경로):
  cd ai/scripts/vocal_analysis

  로컬 파일:  python vocal_analysis_worker.py <job_uuid> -a /path/to.wav
  S3+DB:      python vocal_analysis_worker.py <job_uuid> --aws --s3-key path/in/bucket.m4a
  ECS(RunTask): 환경변수 JOB_ID 만 설정 가능 — s3_key는 analysis_jobs 컬럼 또는 recording_id→recordings.s3_key 조회
  SQS 폴링:   python vocal_analysis_worker.py --queue (로컬·레거시 검증용)

  (venv는 ai 디렉터리에서 생성 후)
  cd ../.. && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
  cd scripts/vocal_analysis && python vocal_analysis_worker.py --queue

  Docker (ai 루트):
  docker compose -f docker-compose.vocal_analysis_worker.yml up --build

  SQS 메시지 Body JSON 예(기본): {"job_id":"<uuid>"} — s3_key 생략 시 DB에서 조회(analysis_jobs 또는 recording_id→recordings)

.env (ai/.env, 다른 테이블/컬럼명일 때만 추가):
  ANALYSIS_JOBS_TABLE=analysis_jobs
  ANALYSIS_JOBS_ID_COLUMN=id
  ANALYSIS_JOBS_TIMESTAMP_COLUMN=updated_at
  ANALYSIS_JOBS_RESULT_COLUMN=result_data
  VOCAL_ANALYSIS_INCLUDE_SCORING_SONG_ALIGNED=1  # 기본 1: user_vocal_profiles 임베딩·f0·timbre 컬럼 채움. 0이면 result_data 용량만 축소
  VOCAL_ANALYSIS_SQS_VISIBILITY_TIMEOUT=1800   # SQS 수신 시 메시지 숨김(초), 0이면 큐 기본값
  VOCAL_ANALYSIS_SQS_WAIT_TIME_SECONDS=20     # long polling (최대 20)
  VOCAL_ANALYSIS_TIMING_LOG=1                 # 0이면 [VOCAL_TIMING] 단계 로그 비활성화

ECS 기동 측정 (Fargate):
  - [ECS_BOOT] APP_BOOT_START: 파이썬이 본 스크립트의 첫 stdout (DescribeTasks startedAt 과 비교)
  - [ECS_BOOT] APP_MODULE_LOADED: 무거운 import·dotenv 이후
  - [ECS_BOOT] PIPELINE_HANDLER_START / WORKER_CONSTRUCT_END: run_aws_job_from_env 진입·VocalAnalysisWorker 생성 직후
  - [VOCAL_TIMING] job_total: 실제 1건 분석 구간
  Lambda 디스패처는 [ECS_DISPATCH] RunTask_submitted 로 T0 를 CloudWatch 에 남김 (ecs_run_task.py).
"""
from __future__ import annotations


def _ecs_boot_ts() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _log_ecs_boot(event: str, **extra: str) -> None:
    """stdlib만 사용 — import 되기 전에도 호출 가능."""
    import os

    jid = (os.environ.get("JOB_ID") or "").strip() or "-"
    parts = [f"[ECS_BOOT] event={event}", f"job_id={jid}", f"ts={_ecs_boot_ts()}"]
    for k, v in extra.items():
        parts.append(f"{k}={v}")
    print(" ".join(parts), flush=True)


_log_ecs_boot(
    "APP_BOOT_START",
    note="before_heavy_imports;delta_from_container_StartedAt_in_DescribeTasks",
)

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
import warnings
warnings.filterwarnings('ignore')

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from report_for_db import build_failure_result_data, build_result_data_payload
from user_song_aligned_features import build_scoring_song_aligned_from_pipeline_result
from user_vocal_pipeline import UserVocalPipeline
from user_vocal_profile_sync import sync_user_vocal_profile_after_job
from vocal_phase_timing import log_phase, timing_job_reset, timing_job_token


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

_log_ecs_boot(
    "APP_MODULE_LOADED",
    note="after_imports_and_dotenv;before_VocalAnalysisWorker_instantiation",
)

# 보컬 분석용 SQS Queue URL (추천과 분리)
VOCAL_ANALYSIS_SQS_QUEUE_URL = os.getenv("VOCAL_ANALYSIS_SQS_QUEUE_URL")

# SQS ReceiveMessage 전용 (메시지별). CPU·ECAPA 분석이 5분을 넘기 쉬워 기본 30분.
# 큐 기본값만 쓰려면 0 → receive_message 에서 생략.
def _sqs_visibility_timeout_for_receive() -> Optional[int]:
    raw = (os.getenv("VOCAL_ANALYSIS_SQS_VISIBILITY_TIMEOUT") or "1800").strip()
    try:
        v = int(raw)
    except ValueError:
        v = 1800
    if v <= 0:
        return None
    return max(60, min(v, 43200))


def _sqs_wait_time_seconds() -> int:
    raw = (os.getenv("VOCAL_ANALYSIS_SQS_WAIT_TIME_SECONDS") or "20").strip()
    try:
        v = int(raw)
    except ValueError:
        v = 20
    return max(0, min(v, 20))


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _output_base_dir() -> str:
    """
    파이프라인 임시·중간 산출물 루트.
    Lambda 는 /var/task 가 읽기 전용이므로 AWS_LAMBDA_FUNCTION_NAME 이 있으면 기본 /tmp 사용.
    """
    explicit = (os.getenv("VOCAL_ANALYSIS_OUTPUT_ROOT") or "").strip()
    if explicit:
        return explicit
    if (os.getenv("AWS_LAMBDA_FUNCTION_NAME") or "").strip():
        return "/tmp/vocal_worker_output"
    return "output"


def _job_output_dir(job_id: str) -> str:
    return str(Path(_output_base_dir()) / job_id)


# 유저 음성 업로드 버킷 (공통 env 사용)
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Supabase analysis_jobs — 프로젝트 기본 스키마에 맞춤 (.env 로 덮어쓰기 가능)
ANALYSIS_JOBS_TABLE = (os.getenv("ANALYSIS_JOBS_TABLE") or "analysis_jobs").strip()
ANALYSIS_JOBS_ID_COLUMN = (os.getenv("ANALYSIS_JOBS_ID_COLUMN") or "id").strip()
ANALYSIS_JOBS_TIMESTAMP_COLUMN = (os.getenv("ANALYSIS_JOBS_TIMESTAMP_COLUMN") or "updated_at").strip()
ANALYSIS_JOBS_RESULT_COLUMN = (os.getenv("ANALYSIS_JOBS_RESULT_COLUMN") or "result_data").strip()
# analysis_jobs.recording_id → recordings.s3_key (큐에 s3_key 없을 때)
ANALYSIS_JOBS_RECORDING_ID_COLUMN = (
    os.getenv("ANALYSIS_JOBS_RECORDING_ID_COLUMN") or "recording_id"
).strip()
RECORDINGS_TABLE = (os.getenv("RECORDINGS_TABLE") or "recordings").strip()
RECORDINGS_ID_COLUMN = (os.getenv("RECORDINGS_ID_COLUMN") or "id").strip()
RECORDINGS_S3_KEY_COLUMN = (os.getenv("RECORDINGS_S3_KEY_COLUMN") or "s3_key").strip()
INCLUDE_SCORING_SONG_ALIGNED = _env_bool("VOCAL_ANALYSIS_INCLUDE_SCORING_SONG_ALIGNED", default=True)

# vocal_analysis_status enum (DB 와 동일하게 대문자)
STATUS_ANALYZING = "ANALYZING"
STATUS_DONE = "DONE"
STATUS_FAILED = "FAILED"


def resolve_s3_key_from_analysis_row(row: Dict) -> Optional[str]:
    """analysis_jobs 한 행에서 오디오 S3 객체 키 후보 컬럼을 순서대로 탐색."""
    for k in (
        "s3_key",
        "audio_s3_key",
        "object_key",
        "storage_path",
        "audio_path",
    ):
        v = row.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def fetch_s3_key_from_recordings(supabase, recording_id: str) -> Optional[str]:
    """
    recordings 테이블에서 오디오 S3 키 조회.
    analysis_jobs의 recording_id(UUID)가 recordings.id와 매칭된다고 가정.
    """
    if not supabase or not recording_id:
        return None
    try:
        res = (
            supabase.table(RECORDINGS_TABLE)
            .select(RECORDINGS_S3_KEY_COLUMN)
            .eq(RECORDINGS_ID_COLUMN, recording_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            print(
                f"⚠️  {RECORDINGS_TABLE} 행 없음: "
                f"{RECORDINGS_ID_COLUMN}={recording_id}"
            )
            return None
        v = rows[0].get(RECORDINGS_S3_KEY_COLUMN)
        if v is not None and str(v).strip():
            return str(v).strip()
    except Exception as e:
        print(f"⚠️  {RECORDINGS_TABLE} 조회 실패 (recording_id={recording_id}): {e}")
    return None


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
        self.include_scoring_song_aligned = INCLUDE_SCORING_SONG_ALIGNED
        
        # 보컬 분석 파이프라인 초기화
        self.pipeline = UserVocalPipeline()
        
        print("🎤 보컬 분석 워커 초기화 완료")
        if use_aws:
            print("  - AWS 모드: S3 + DB 연동")
            print(
                "  - result_data.scoring_song_aligned 포함: "
                f"{'ON' if self.include_scoring_song_aligned else 'OFF'} "
                "(env VOCAL_ANALYSIS_INCLUDE_SCORING_SONG_ALIGNED)"
            )
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

        _tj = timing_job_token(job_id)
        temp_download_path: Optional[Path] = None
        _job_total_started = False
        try:
            if self.use_aws:
                row0 = self._fetch_analysis_job_row(job_id)
                if row0:
                    st = (row0.get("status") or "").strip().upper()
                    if st == STATUS_DONE:
                        print(f"⏭️  이미 DONE — 중복 실행 스킵: job_id={job_id}")
                        return {
                            "status": "skipped",
                            "job_id": job_id,
                            "reason": "already DONE",
                        }
                    if not (s3_key or "").strip():
                        s3_key = resolve_s3_key_from_analysis_row(row0) or s3_key
                    if (
                        not (s3_key or "").strip()
                        and row0
                        and ANALYSIS_JOBS_RECORDING_ID_COLUMN
                    ):
                        rid = row0.get(ANALYSIS_JOBS_RECORDING_ID_COLUMN)
                        if rid is not None and str(rid).strip():
                            s3_key = fetch_s3_key_from_recordings(
                                self.supabase, str(rid).strip()
                            ) or s3_key

            if self.use_aws:
                try:
                    self._patch_analysis_job(job_id, {"status": STATUS_ANALYZING})
                except Exception as db_err:
                    print(f"⚠️  DB 상태 ANALYZING 반영 실패 (행 없음·RLS 등): {db_err}")

            log_phase("job_total", "START")
            _job_total_started = True

            # Step 1: 오디오 파일 가져오기
            if self.use_aws:
                if not s3_key:
                    raise ValueError(
                        "AWS 모드에서는 s3_key가 필요합니다 "
                        "(메시지/인자, analysis_jobs의 s3_key 계열 컬럼, "
                        f"{ANALYSIS_JOBS_RECORDING_ID_COLUMN}→{RECORDINGS_TABLE}.{RECORDINGS_S3_KEY_COLUMN}, "
                        "또는 S3_KEY 환경변수)"
                    )
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
            out_base = _job_output_dir(job_id)
            Path(out_base).mkdir(parents=True, exist_ok=True)
            analysis_result = self.pipeline.process(
                audio_path=audio_file,
                output_dir=out_base,
                save_features=True,
            )
            
            # Step 3: 결과 저장 — 로컬만 JSON 파일, AWS는 DB만
            if self.use_aws:
                log_phase("db_save", "START", note="analysis_jobs+profile_sync")
                self._save_to_db(job_id, analysis_result)
                log_phase("db_save", "END")
                # Fargate/도커/Lambda 디스크 누적 방지: 파이프라인이 쓴 작업 디렉터리 제거
                out_dir = Path(out_base)
                if out_dir.is_dir():
                    shutil.rmtree(out_dir, ignore_errors=True)
            else:
                output_file = str(Path(out_base) / "result.json")
                log_phase("result_save", "START", note="local_json")
                self._save_to_json(analysis_result, output_file)
                log_phase("result_save", "END")
                print(f"\n[Step 3] 결과 저장: {output_file}")
            
            print("\n" + "="*70)
            print(f"✅ 작업 완료: job_id={job_id}")
            print("="*70)

            if _job_total_started:
                log_phase("job_total", "END", note="status=success")
            return {
                'status': 'success',
                'job_id': job_id,
                'result': analysis_result
            }
            
        except Exception as e:
            print(f"\n❌ 작업 실패: {e}")
            import traceback
            traceback.print_exc()
            if _job_total_started:
                log_phase("job_total", "END", note="status=failed")

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
            try:
                timing_job_reset(_tj)
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
            log_phase("s3_download", "START", job_id=job_id)
            try:
                s3.download_file(self.s3_bucket, s3_key, str(tmp_path))
            finally:
                log_phase("s3_download", "END", job_id=job_id)
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

    def _fetch_job_context(self, job_id: str) -> Dict:
        """analysis_jobs 한 행에서 user_id 조회 (프로필 UPSERT용). 메타는 result_data에 넣지 않음."""
        row = self._fetch_analysis_job_row(job_id)
        if not row:
            return {}
        uid = row.get("user_id")
        return {"user_id": uid} if uid is not None else {}

    def _fetch_analysis_job_row(self, job_id: str) -> Optional[Dict]:
        """analysis_jobs 전체 컬럼 조회 (상태·s3_key 후보 확인용)."""
        if not self.supabase:
            return None
        try:
            res = (
                self.supabase.table(ANALYSIS_JOBS_TABLE)
                .select("*")
                .eq(ANALYSIS_JOBS_ID_COLUMN, job_id)
                .limit(1)
                .execute()
            )
            rows = res.data or []
            return rows[0] if rows else None
        except Exception as e:
            print(f"⚠️  analysis_jobs 행 조회 실패: {e}")
            return None

    def _save_to_db(self, job_id: str, result: Dict):
        """
        분석 결과를 DB(Supabase analysis_jobs)에 저장 — status=DONE, result_data=jsonb
        """
        print(f"\n[Step 3] DB에 저장 중 (화면용 result_data, 메타는 행 컬럼만)...")
        print(f"  - {ANALYSIS_JOBS_ID_COLUMN}: {job_id}")

        result_data = build_result_data_payload(result)
        if self.include_scoring_song_aligned:
            aligned = build_scoring_song_aligned_from_pipeline_result(result)
            if aligned:
                result_data["scoring_song_aligned"] = aligned

        self._patch_analysis_job(
            job_id,
            {"status": STATUS_DONE, ANALYSIS_JOBS_RESULT_COLUMN: result_data},
        )

        ctx = self._fetch_job_context(job_id)
        sync_user_vocal_profile_after_job(
            self.supabase, user_id=ctx.get("user_id")
        )

    def _mark_job_failed(self, job_id: str, error_message: str):
        """
        실패 시 status=FAILED, 에러는 error_message 컬럼 없음 → result_data 에 JSON 으로 저장
        """
        print(f"\n[Step 3] DB에 실패 상태 저장 중...")
        print(f"  - {ANALYSIS_JOBS_ID_COLUMN}: {job_id}")
        print(f"  - error: {error_message}")

        fail_data = build_failure_result_data(error_message)
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
# ECS RunTask / Lambda 디스패처용 (SQS 폴링 없이 1건 실행)
# ============================================================================


def run_aws_job_from_env() -> Dict:
    """
    환경변수 JOB_ID 필수. S3_KEY 또는 AUDIO_S3_KEY 가 있으면 우선 사용, 없으면 analysis_jobs 행에서 키 조회.
    """
    job_id = (os.getenv("JOB_ID") or "").strip()
    if not job_id:
        raise RuntimeError("JOB_ID 환경변수가 필요합니다.")
    sk = (os.getenv("S3_KEY") or os.getenv("AUDIO_S3_KEY") or "").strip() or None
    _log_ecs_boot(
        "PIPELINE_HANDLER_START",
        note="before_VocalAnalysisWorker_ctor",
    )
    worker = VocalAnalysisWorker(use_aws=True)
    _log_ecs_boot(
        "WORKER_CONSTRUCT_END",
        note="before_process_job;includes_UserVocalPipeline_init",
    )
    return worker.process_job(job_id, s3_key=sk)


# ============================================================================
# SQS 연동 (추천 워커와 유사한 비동기 파이프라인)
# ============================================================================

def receive_message_from_queue(
    sqs_client,
    queue_url: str,
    *,
    visibility_timeout: Optional[int],
    wait_time_seconds: int = 20,
) -> Optional[Dict]:
    """
    SQS Queue에서 보컬 분석 작업 메시지 수신

    기대 메시지 형식 (JSON Body):
    {
        "job_id": "...",        # 필수 (analysis_jobs.id 와 동일 UUID)
        "id": "...",            # 위와 동일 (대체 필드)
        "s3_key": "...",        # 선택 — 없으면 analysis_jobs 또는 recordings 에서 조회
    }
    실패 시 메시지는 삭제하지 않음 → 재시도. 반복 실패는 SQS DLQ 설정 권장.
    """
    try:
        recv_kw: Dict = {
            "QueueUrl": queue_url,
            "MaxNumberOfMessages": 1,
            "WaitTimeSeconds": wait_time_seconds,
        }
        if visibility_timeout is not None:
            recv_kw["VisibilityTimeout"] = visibility_timeout
        response = sqs_client.receive_message(**recv_kw)

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
    vis = _sqs_visibility_timeout_for_receive()
    wait_s = _sqs_wait_time_seconds()

    print("\n" + "=" * 70)
    print("🚀 보컬 분석 SQS 워커 시작")
    print("=" * 70)
    print(f"  - Queue URL: {VOCAL_ANALYSIS_SQS_QUEUE_URL}")
    if vis is not None:
        print(f"  - SQS VisibilityTimeout (per message): {vis}s (env VOCAL_ANALYSIS_SQS_VISIBILITY_TIMEOUT)")
    else:
        print("  - SQS VisibilityTimeout: (queue default; VOCAL_ANALYSIS_SQS_VISIBILITY_TIMEOUT<=0)")
    print(f"  - Long polling WaitTimeSeconds: {wait_s}")
    print("=" * 70 + "\n")

    import time

    while True:
        try:
            message = receive_message_from_queue(
                sqs_client,
                VOCAL_ANALYSIS_SQS_QUEUE_URL,
                visibility_timeout=vis,
                wait_time_seconds=wait_s,
            )

            if not message:
                print("대기 중... (메시지 없음)")
                time.sleep(5)
                continue

            job_id = message.get("job_id")
            sk_raw = message.get("s3_key")
            s3_key = (
                str(sk_raw).strip()
                if sk_raw is not None and str(sk_raw).strip()
                else None
            )

            if not job_id:
                print("⚠️  필수 필드 누락: job_id — 메시지 삭제(재시도 무의미)")
                delete_message_from_queue(
                    sqs_client,
                    VOCAL_ANALYSIS_SQS_QUEUE_URL,
                    message["receipt_handle"],
                )
                continue

            print(
                f"\n📨 메시지 수신: job_id={job_id}"
                + (f", s3_key={s3_key}" if s3_key else " (s3_key는 DB 조회)")
            )

            # 실제 보컬 분석 처리 — s3_key 없으면 process_job 내에서 DB 조회
            result = worker.process_job(
                job_id=str(job_id).strip(), s3_key=s3_key
            )

            if result.get("status") in ("success", "skipped"):
                print(f"✅ 작업 완료: {job_id}" + (" (skipped)" if result.get("status") == "skipped" else ""))
                # 성공·이미 처리됨 시 삭제 (실패 시 visibility timeout 후 재시도 / DLQ 정책에 맡김)
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
        help="(레거시) SQS 폴링 — 프로덕션은 Lambda + RunTask 및 환경변수 JOB_ID",
    )

    args = parser.parse_args()

    # 워커 실행
    try:
        job_id_env = (os.getenv("JOB_ID") or "").strip()

        if args.queue:
            run_worker_loop()
        elif args.job_id:
            if args.aws:
                if not args.s3_key:
                    print(
                        "ℹ️  --s3-key 생략: analysis_jobs 행에서 오디오 키 컬럼 조회를 시도합니다."
                    )
            else:
                if not args.audio:
                    print("❌ 로컬 모드에서는 --audio 가 필요합니다.")
                    sys.exit(1)

            worker = VocalAnalysisWorker(use_aws=args.aws)
            if args.aws:
                sk = args.s3_key.strip() if args.s3_key else None
                result = worker.process_job(args.job_id, s3_key=sk)
            else:
                result = worker.process_job(args.job_id, audio_path=args.audio)

            if result["status"] in ("success", "skipped"):
                print("\n✅ 처리 완료!")
                sys.exit(0)
            print(f"\n❌ 처리 실패: {result.get('error', 'unknown')}")
            sys.exit(1)
        elif job_id_env:
            print(f"📌 ECS/JOB_ID 모드: job_id={job_id_env}")
            result = run_aws_job_from_env()
            if result["status"] in ("success", "skipped"):
                print("\n✅ 처리 완료!")
                sys.exit(0)
            print(f"\n❌ 처리 실패: {result.get('error', 'unknown')}")
            sys.exit(1)
        else:
            print(
                "❌ Positional job_id, 또는 환경변수 JOB_ID, 또는 --queue 가 필요합니다."
            )
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

