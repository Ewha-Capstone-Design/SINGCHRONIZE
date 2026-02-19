"""
유저 보컬 전처리 메인 파이프라인 (아카펠라 전용)
- 1번의 전처리로 리포트 + 추천용 데이터 동시 생성
- 사용자가 아카펠라로만 녹음하므로 MR 제거 불필요
"""
import json
from pathlib import Path
from typing import Dict, Optional
import warnings
warnings.filterwarnings('ignore')

from audio_preprocessing import AudioPreprocessor
from feature_extraction import FeatureExtractor
from report_generator_v2 import ReportGeneratorV2
from radar_chart_descriptions import RADAR_CHART_DESCRIPTIONS, get_score_interpretation


class UserVocalPipeline:
    """
    유저 보컬 전처리 통합 파이프라인 (아카펠라 전용)
    
    ⚠️ 중요: 사용자는 반드시 아카펠라로만 녹음해야 합니다!
    
    기능:
    1. 오디오 전처리 (표준화 + 세그먼트화)
    2. 특징 추출 (Pitch, Energy, Onset, Timbre, ECAPA)
    3. 보컬 분석 리포트 생성
    4. 추천용 임베딩 생성
    
    사용 예시:
    ```python
    pipeline = UserVocalPipeline()
    result = pipeline.process("user_acapella.wav")
    
    # 리포트
    print(result['report'])
    
    # 추천용 임베딩
    embedding = result['embedding']
    ```
    """
    
    def __init__(
        self,
        sr: int = 16000,
        segment_duration: float = 20.0,
        hop_duration: float = 5.0,
        fast_mode: bool = False
    ):
        """
        Args:
            sr: 샘플레이트 (16kHz 권장)
            segment_duration: 세그먼트 길이 (초)
            hop_duration: 세그먼트 간격 (초)
            fast_mode: 빠른 모드 (세그먼트 길이 증가, 간격 증가로 세그먼트 개수 감소)
        """
        self.sr = sr
        
        # 빠른 모드: 세그먼트 설정 최적화 (30-40초 녹음에 최적화)
        if fast_mode:
            segment_duration = 15.0  # 20초 → 15초 (짧은 녹음에 적합)
            hop_duration = 8.0       # 5초 → 8초 (적당한 overlap)
            print("⚡ 빠른 모드 활성화: 세그먼트 설정 최적화")
            print(f"   - 세그먼트 길이: {segment_duration}초 (30-40초 녹음에 최적화)")
            print(f"   - 세그먼트 간격: {hop_duration}초")
        
        # 모듈 초기화
        self.preprocessor = AudioPreprocessor(
            target_sr=sr,
            segment_duration=segment_duration,
            hop_duration=hop_duration
        )
        self.extractor = FeatureExtractor(sr=sr)
        self.generator = ReportGeneratorV2()
    
    def process(
        self,
        audio_path: str,
        output_dir: Optional[str] = None,
        save_features: bool = True
    ) -> Dict:
        """
        유저 보컬 전체 처리 (아카펠라 전용)
        
        Args:
            audio_path: 입력 아카펠라 오디오 파일 경로
            output_dir: 출력 디렉토리 (None이면 입력 파일과 같은 디렉토리)
            save_features: 특징을 JSON으로 저장할지 여부
        
        Returns:
            result: {
                'report': 보컬 분석 리포트,
                'embedding': 추천용 임베딩,
                'features': 원본 특징 (선택),
                'metadata': 메타데이터
            }
        """
        print("\n" + "="*70)
        print("🎤 SINGCHRONIZE 유저 보컬 전처리 파이프라인 (아카펠라 전용)")
        print("="*70)
        print("⚠️  주의: 반드시 아카펠라(MR 없이 목소리만)로 녹음해주세요!")
        print("="*70)
        
        # 출력 디렉토리 설정
        if output_dir is None:
            output_dir = Path(audio_path).parent / "output"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Step 1: 전처리
        print("\n[Step 1] 오디오 전처리")
        audio, segments = self.preprocessor.preprocess(
            audio_path=audio_path,
            output_dir=str(output_path)
        )
        
        # Step 2: 특징 추출
        print("\n[Step 2] 특징 추출")
        features = self.extractor.extract_all_features(audio, segments)
        
        # Step 3: 리포트 생성
        print("\n[Step 3] 보컬 분석 리포트 생성")
        report = self.generator.generate_report(features)
        
        # Step 4: 추천용 임베딩 준비
        print("\n[Step 4] 추천용 데이터 준비")
        embedding_data = {
            'representative_embedding': features['embedding']['representative'],
            'embedding_dim': features['embedding']['embedding_dim'],
            'pitch_profile': {
                'f0_min': features['pitch']['f0_min'],
                'f0_max': features['pitch']['f0_max'],
                'tessitura_low': features['pitch']['tessitura_low'],
                'tessitura_high': features['pitch']['tessitura_high']
            },
            'timbre_vector': features['timbre']['weighted']
        }
        print(f"✓ 추천용 임베딩 준비 완료 ({embedding_data['embedding_dim']}차원)")
        
        # 결과 구성
        result = {
            'report': report,
            'embedding': embedding_data,
            'metadata': {
                'audio_path': str(audio_path),
                'duration': len(audio) / self.sr,
                'num_segments': len(segments),
                'sample_rate': self.sr
            }
        }
        
        # 특징 저장 (선택)
        if save_features:
            result['features'] = features
        
        # JSON 저장
        output_file = output_path / f"{Path(audio_path).stem}_result.json"
        self._save_result(result, output_file)
        
        print("\n" + "="*70)
        print("✅ 전체 파이프라인 완료!")
        print(f"📁 결과 저장: {output_file}")
        print("="*70 + "\n")
        
        # 요약 출력
        self._print_summary(result)
        
        return result
    
    def _save_result(self, result: Dict, output_file: Path):
        """결과를 JSON으로 저장"""
        # numpy array를 list로 변환 (JSON 직렬화 가능하도록)
        def convert_to_serializable(obj):
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            elif hasattr(obj, 'tolist'):  # numpy array
                return obj.tolist()
            else:
                return obj
        
        serializable_result = convert_to_serializable(result)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 결과 저장 완료: {output_file}")
    
    def _print_summary(self, result: Dict):
        """결과 요약 출력"""
        print("\n" + "="*70)
        print("📊 분석 결과 요약")
        print("="*70)
        
        # 레이더 차트 (안정형 MVP)
        print("\n[레이더 차트 점수]")
        radar = result['report']['radar_chart']
        
        metrics = [
            ('pitch_stability', '🎯', '음정 안정도'),
            ('rhythm_stability', '🎵', '리듬 안정도'),
            ('dynamic_control', '📊', '강약 조절'),
            ('vocal_clarity', '💎', '발성 선명도'),
            ('high_note_stability', '🎤', '고음 유지력')
        ]
        
        for metric_key, emoji, name in metrics:
            score = radar[metric_key]
            interpretation = get_score_interpretation(score)
            desc = RADAR_CHART_DESCRIPTIONS[metric_key]['short_desc']
            print(f"  {emoji} {name}: {score:.1f}/100 ({interpretation})")
            print(f"     → {desc}")
        
        print(f"\n  ⭐ 평균 점수: {radar['average']:.1f}/100 ({get_score_interpretation(radar['average'])})")
        
        # 음역대
        print("\n[음역대 분석]")
        vr = result['report']['vocal_range']
        print(f"  최저음: {vr['lowest_note']} ({vr['lowest_hz']:.1f}Hz)")
        print(f"  최고음: {vr['highest_note']} ({vr['highest_hz']:.1f}Hz)")
        print(f"  테시투라: {vr['tessitura_low_note']} ~ {vr['tessitura_high_note']}")
        print(f"  음역대: {vr['range_semitones']:.1f} 반음")
        
        # 음색
        print("\n[음색 프로파일]")
        timbre = result['report']['timbre_profile']
        
        # 전체 요약
        if 'summary' in timbre:
            print(f"  📝 전체 요약: {timbre['summary']}")
            print()
        
        # 각 축별 설명
        for key, value in timbre.items():
            if key in ['summary', 'formants']:  # summary와 formants는 별도 처리
                continue
            emoji = {
                'brightness': '✨',
                'roughness': '🌊',
                'body': '💪',
                'clarity': '💎',
                'warmth': '🔥',
                'richness': '🎭',
                'texture': '🌈'
            }.get(key, '•')
            
            # interpretation 키가 있으면 표시, 없으면 생략
            if 'interpretation' in value:
                print(f"  {emoji} {key} ({value['interpretation']})")
            else:
                print(f"  {emoji} {key}")
            print(f"     → {value['description']}")
        
        # 장르별 적합도
        print("\n[장르별 적합도 TOP 3]")
        genre_fitness = result['report']['genre_fitness']
        for i, genre_info in enumerate(genre_fitness['top_genres'], 1):
            print(f"  {i}. {genre_info['genre']}: {genre_info['score']:.1f}/100")
            print(f"     → {genre_info['description']}")
            print(f"     → 이유: {genre_info['reason']}")
        
        # 메타데이터
        print("\n[메타데이터]")
        meta = result['metadata']
        print(f"  길이: {meta['duration']:.2f}초")
        print(f"  세그먼트: {meta['num_segments']}개")
        print(f"  샘플레이트: {meta['sample_rate']}Hz")
        
        print("="*70 + "\n")


def process_single_file(audio_path: str, output_dir: str = None):
    """
    단일 파일 처리 헬퍼 함수 (아카펠라 전용)
    
    Args:
        audio_path: 아카펠라 오디오 파일 경로
        output_dir: 출력 디렉토리
    
    Returns:
        result: 처리 결과
    """
    pipeline = UserVocalPipeline()
    result = pipeline.process(audio_path, output_dir=output_dir)
    return result


def process_batch(audio_paths: list, output_dir: str = None):
    """
    배치 처리 헬퍼 함수
    
    Args:
        audio_paths: 오디오 파일 경로 리스트
        output_dir: 출력 디렉토리
    
    Returns:
        results: 처리 결과 리스트
    """
    pipeline = UserVocalPipeline()
    results = []
    
    for i, audio_path in enumerate(audio_paths, 1):
        print(f"\n{'='*70}")
        print(f"처리 중: [{i}/{len(audio_paths)}] {audio_path}")
        print(f"{'='*70}")
        
        try:
            result = pipeline.process(audio_path, output_dir=output_dir)
            results.append({
                'audio_path': audio_path,
                'status': 'success',
                'result': result
            })
        except Exception as e:
            print(f"❌ 처리 실패: {e}")
            results.append({
                'audio_path': audio_path,
                'status': 'failed',
                'error': str(e)
            })
    
    # 배치 요약
    print("\n" + "="*70)
    print("📊 배치 처리 완료")
    print("="*70)
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"✅ 성공: {success_count}/{len(audio_paths)}")
    print(f"❌ 실패: {len(audio_paths) - success_count}/{len(audio_paths)}")
    print("="*70 + "\n")
    
    return results


# CLI 실행
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SINGCHRONIZE 유저 보컬 전처리 파이프라인"
    )
    parser.add_argument(
        "audio_path",
        type=str,
        help="입력 오디오 파일 경로"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="출력 디렉토리 (기본값: 입력 파일과 같은 디렉토리/output)"
    )
    parser.add_argument(
        "--no-save-features",
        action="store_true",
        help="특징 저장 비활성화"
    )
    
    args = parser.parse_args()
    
    # 파일 존재 확인
    if not Path(args.audio_path).exists():
        print(f"❌ 파일을 찾을 수 없습니다: {args.audio_path}")
        sys.exit(1)
    
    # 파이프라인 실행
    try:
        pipeline = UserVocalPipeline()
        result = pipeline.process(
            audio_path=args.audio_path,
            output_dir=args.output,
            save_features=not args.no_save_features
        )
        
        print("\n✅ 처리 완료!")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

