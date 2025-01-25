from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import logging

def calculate_similarity(text1, text2):
    """
    두 텍스트 간의 코사인 유사도를 계산합니다.
    Args:
        text1 (str): 첫 번째 텍스트
        text2 (str): 두 번째 텍스트
    Returns:
        float: 유사도 값 (0~1 사이)
    """
    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    similarity = cosine_similarity([vectors[0]], [vectors[1]])
    return similarity[0][0]

logger = logging.getLogger('django')

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
            if ":" in line:  # "키: 값" 형태로 구분
                key, value = line.split(":", 1)
                current_item[key.strip()] = value.strip()
            elif not line:  # 빈 줄이면 새로운 항목 시작
                if current_item:
                    parsed_data.append(current_item)
                    current_item = {}
        if current_item:  # 마지막 항목 추가
            parsed_data.append(current_item)
        return parsed_data