"""
레이더 차트 5축 설명
- 유저가 이해할 수 있는 언어로 작성
"""

RADAR_CHART_DESCRIPTIONS = {
    'pitch_stability': {
        'name': '음정 안정도',
        'short_desc': '한 음을 얼마나 흔들림 없이 유지하는가',
        'long_desc': '한 음을 낼 때 그 음이 얼마나 흔들리지 않고 유지되는지를 측정합니다. (순수 보컬 품질)',
        'high_example': '한 음을 길게 끌어도 떨림이 거의 없고, 음이 위아래로 흔들리지 않습니다. 청자 입장에서 "안정적이다", "차분하다"는 느낌을 줍니다.',
        'low_example': '한 음을 유지하는데 계속 미묘하게 위아래로 흔들리거나, 음 끝에서 힘이 빠지며 pitch가 떨어집니다. "불안하다", "힘이 부족하다"는 느낌을 줍니다.',
        'measurement': 'MR 제거 후 순수 보컬에서 F0(주파수)를 추출하여 한 음 안에서 표준편차를 계산합니다. 흔들림이 적을수록 점수가 높습니다.',
        'note': '※ 음정의 "안정성"을 측정 (흔들림). 음정의 "정확도"는 별도 측정 (MR 포함 분석)'
    },
    
    'rhythm_stability': {
        'name': '리듬 안정도',
        'short_desc': '자기 템포를 얼마나 일정하게 유지하는가',
        'long_desc': '노래하는 동안 자신의 템포를 얼마나 일정하게 유지하는지를 측정합니다. (순수 보컬 품질)',
        'high_example': '박자를 재지 않아도 일정한 템포로 노래하며, 프레이즈마다 길이가 비슷하고 점점 빨라지거나 느려지지 않습니다.',
        'low_example': '긴장하면 빨라지거나 후반부 갈수록 느려지며, 음절마다 길이가 들쭉날쭉합니다.',
        'measurement': 'MR 제거 후 순수 보컬에서 Onset(소리 시작점)을 추출하여 IOI(간격)를 계산합니다. 간격 변동이 적을수록 점수가 높습니다.',
        'note': '※ 리듬의 "안정성"을 측정 (일정함). 리듬의 "정확도"는 별도 측정 (MR 포함 분석)'
    },
    
    'dynamic_control': {
        'name': '강약 조절',
        'short_desc': '소리 크기를 얼마나 자연스럽게 조절하는가',
        'long_desc': '소리를 크고 작게 조절할 수 있는 능력을 측정합니다.',
        'high_example': '도입부는 작게, 후렴은 크게 부르며 감정에 따라 강약 변화가 자연스럽습니다. 입체적인 노래가 됩니다.',
        'low_example': '처음부터 끝까지 비슷한 크기로 부르거나, 갑자기 확 커지거나 급격히 줄어들어 부자연스럽습니다.',
        'measurement': 'RMS(에너지)를 분석하여 전체 다이나믹 범위와 RMS 변화의 부드러움을 측정합니다.'
    },
    
    'vocal_clarity': {
        'name': '발성 선명도',
        'short_desc': '소리가 얼마나 또렷하고 깨끗한가',
        'long_desc': '목소리가 얼마나 또렷하고 깨끗한지, 즉 소리 속 잡음이 얼마나 적은지를 측정합니다.',
        'high_example': '음이 또렷하게 들리고 공명이 잘 울리며 소리가 맑습니다. HNR(조화 성분)이 높습니다.',
        'low_example': '쉰 느낌이 있거나 숨소리가 많고, 소리가 퍼지고 흐릿합니다. 잡음 성분이 많습니다.',
        'measurement': 'HNR(Harmonics-to-Noise Ratio)로 조화음과 잡음의 비율을 측정합니다. 비율이 높을수록 점수가 높습니다.'
    },
    
    'high_note_stability': {
        'name': '고음 유지력',
        'short_desc': '높은 음에서도 안정성이 유지되는가',
        'long_desc': '높은 음을 낼 때 얼마나 무너지지 않는지를 측정합니다. 단순히 "고음을 낼 수 있느냐"가 아니라 "높은 음에서도 안정성을 유지하는가"를 봅니다.',
        'high_example': '고음에서도 pitch 흔들림이 적고, 소리가 얇아지지 않으며, HNR이 급감하지 않고 에너지가 유지됩니다.',
        'low_example': '고음에서 소리가 얇아지거나 음정이 불안해지고, 숨이 섞이며 소리가 갑자기 작아집니다.',
        'measurement': '고음 구간(상위 25% F0)을 필터링하여 해당 구간에서 pitch 표준편차, HNR 유지 여부, RMS 유지 여부를 측정합니다.'
    }
}

def get_score_interpretation(score: float) -> str:
    """점수에 따른 해석"""
    if score >= 90:
        return "매우 우수"
    elif score >= 80:
        return "우수"
    elif score >= 70:
        return "양호"
    elif score >= 60:
        return "보통"
    elif score >= 50:
        return "개선 필요"
    else:
        return "많은 연습 필요"

def get_detailed_feedback(metric: str, score: float) -> str:
    """점수에 따른 상세 피드백"""
    desc = RADAR_CHART_DESCRIPTIONS.get(metric, {})
    
    if score >= 70:
        return f"✅ {desc.get('high_example', '')}"
    else:
        return f"💡 개선 포인트: {desc.get('low_example', '')}"

# ========================================
# 하이브리드 분석: 음정/리듬 정확도
# ========================================

ACCURACY_DESCRIPTIONS = {
    'pitch_accuracy': {
        'name': '음정 정확도',
        'short_desc': 'MR 멜로디를 얼마나 정확하게 따라 부르는가',
        'long_desc': 'MR의 멜로디(정답 음정)와 비교하여 얼마나 정확하게 부르는지를 측정합니다.',
        'high_example': 'MR 멜로디와 거의 일치하게 부릅니다. 음정이 정확하고 틀리는 구간이 거의 없습니다.',
        'low_example': 'MR 멜로디와 차이가 있습니다. 음정이 높거나 낮게 나가는 구간이 있습니다.',
        'measurement': 'MR 포함 오디오에서 F0를 추출하여 안정성을 측정합니다. MR 멜로디와 함께 부르면 F0가 더 안정적이므로, 안정성이 높을수록 정확도가 높습니다.',
        'vs_stability': '※ "음정 안정도"는 흔들림을 측정, "음정 정확도"는 정답 대비 정확성을 측정'
    },
    
    'rhythm_accuracy': {
        'name': '리듬 정확도',
        'short_desc': 'MR 박자를 얼마나 정확하게 맞추는가',
        'long_desc': 'MR의 박자(정답 리듬)와 비교하여 얼마나 정확하게 맞추는지를 측정합니다.',
        'high_example': 'MR 박자와 거의 일치하게 부릅니다. 박자가 정확하고 늦거나 빠른 구간이 거의 없습니다.',
        'low_example': 'MR 박자와 차이가 있습니다. 늦게 들어가거나 빠르게 부르는 구간이 있습니다.',
        'measurement': 'MR 포함 오디오에서 Onset을 추출하여 규칙성을 측정합니다. MR 박자와 함께 부르면 Onset이 더 규칙적이므로, 규칙성이 높을수록 정확도가 높습니다.',
        'vs_stability': '※ "리듬 안정도"는 일정함을 측정, "리듬 정확도"는 정답 대비 정확성을 측정'
    }
}

def get_accuracy_interpretation(accuracy_type: str, score: float) -> str:
    """정확도 점수 해석"""
    desc = ACCURACY_DESCRIPTIONS.get(accuracy_type, {})
    
    if score >= 90:
        level = "매우 정확"
    elif score >= 80:
        level = "정확"
    elif score >= 70:
        level = "양호"
    elif score >= 60:
        level = "보통"
    else:
        level = "개선 필요"
    
    return f"{desc['name']}: {level}"
