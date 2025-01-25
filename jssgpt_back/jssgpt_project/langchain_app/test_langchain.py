import os
import django
import sys

# Django 설정 로드
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jssgpt_project.settings")
django.setup()

from langchain_app.utils import generate_and_save_company_info

# OpenAI API 키 설정
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"

def test_generate_company_info():
    company_name = "코리아크레딧뷰로"
    result = generate_and_save_company_info(company_name)
    print("[TEST] Generated Company Info:", result)

if __name__ == "__main__":
    test_generate_company_info()
