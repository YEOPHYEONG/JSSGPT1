import sys
import asyncio
import json
import logging
from langchain_app.crawler import integrated_crawler
import os

# 모든 로그를 stderr로 출력 (stdout에는 순수 JSON만)
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            logging.error("Usage: python crawler_script.py YYYYMMDD")
            sys.exit(1)
        target_date = sys.argv[1]
        logging.info(f"Starting crawler for target_date: {target_date}")
        
        # 현재 작업 디렉터리 디버깅 출력
        logging.debug(f"Current working directory in crawler_script.py: {os.getcwd()}")
        
        # 크롤링 실행 – integrated_crawler 내부에서 발생하는 예외는 여기서 잡힘
        companies_data = asyncio.run(integrated_crawler(target_date))
        logging.info("Crawler finished successfully.")
        
        # 오직 순수 JSON 데이터만 stdout으로 출력
        print(json.dumps(companies_data))
    except Exception as e:
        logging.exception(f"Exception occurred in crawler_script.py: {e}")
        sys.exit(2)
