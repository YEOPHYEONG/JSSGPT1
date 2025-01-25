from django.test import TestCase
from .utils import generate_and_save_data
from .models import GeneratedData

class LangChainTestCase(TestCase):
    def test_generate_and_save_data(self):
        # 테스트용 프롬프트
        prompt = "Explain the benefits of using LangChain with Django."
        
        # 데이터 생성 및 저장 호출
        generated_data = generate_and_save_data(prompt)
        
        # 데이터베이스에 저장되었는지 확인
        self.assertEqual(GeneratedData.objects.count(), 1)
        self.assertEqual(generated_data.prompt, prompt)
        print("Generated Response:", generated_data.response)
