import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI

# .env 파일 로드
load_dotenv()

def test_langchain():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # ChatOpenAI 클래스 사용 (최신 방식)
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7, openai_api_key=openai_api_key)
    
    # 새로운 방식으로 호출
    result = llm.invoke("Say hello in Korean")
    print(result)

if __name__ == "__main__":
    test_langchain()
