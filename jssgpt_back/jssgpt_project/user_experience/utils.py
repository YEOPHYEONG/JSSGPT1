from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import logging

logger = logging.getLogger('django')

def calculate_similarity(text1, text2):
    """
    두 텍스트 간의 코사인 유사도를 계산합니다.
    Args:
        text1 (str): 첫 번째 텍스트
        text2 (str): 두 번째 텍스트
    Returns:
        float: 유사도 값 (0~1 사이)
    """
    # 플레이스홀더 텍스트인 경우 비교하지 않음
    placeholder = "경험을 입력해주세요"
    if text1.strip() == placeholder or text2.strip() == placeholder:
        return 0.0
    try:
        vectorizer = TfidfVectorizer().fit_transform([text1, text2])
        vectors = vectorizer.toarray()
        similarity = cosine_similarity([vectors[0]], [vectors[1]])
        return similarity[0][0]
    except ValueError as e:
        logger.warning(f"Similarity calculation error: {e}")
        return 0.0

def parse_openai_response(response):
    """
    OpenAI 응답을 JSON 형태로 파싱합니다.
    JSON 형식이 아닐 경우, 텍스트를 파싱하여 딕셔너리로 변환.
    """
    try:
        # JSON 형식인지 확인하고 파싱
        return json.loads(response)
    except json.JSONDecodeError:
        # JSON이 아닐 경우 텍스트 파싱
        logger.warning("OpenAI Response is not JSON. Attempting to parse manually.")
        parsed_data = []
        lines = response.split("\n")
        current_item = {}
        for line in lines:
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                # 키와 값을 깨끗하게 정리 (따옴표, 쉼표 제거)
                key = key.strip().strip('"')
                value = value.strip().strip('",')
                current_item[key] = value
            elif not line:
                if current_item:
                    parsed_data.append(current_item)
                    current_item = {}
        if current_item:
            parsed_data.append(current_item)
        return parsed_data
