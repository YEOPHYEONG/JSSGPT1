# crawler.py

import sys # sys import 추가
import datetime # datetime import 추가
import asyncio # asyncio import 추가 (for wait_for_timeout)
import json
import logging
import os
from playwright.async_api import async_playwright

logging.basicConfig(stream=sys.stderr, level=logging.INFO) # 로그 레벨 INFO 또는 DEBUG 확인
logger = logging.getLogger(__name__)

async def ensure_logged_in(playwright):
    # ... (ensure_logged_in 함수 내용은 기존과 동일하게 유지) ...
    if os.path.exists("state.json"):
        logger.info("이미 로그인 상태가 저장되어 있습니다.")
        return

    browser = await playwright.chromium.launch(
        headless=True,
        args=["--disable-extensions", "--disable-gpu", "--disable-dev-shm-usage"]
    )
    context = await browser.new_context(viewport={"width": 800, "height": 600})
    page = await context.new_page()
    await page.goto("https://jasoseol.com/")
    try:
        await page.click("div[data-sentry-component='PopupAdvertise'] button", timeout=10000)
        logger.info("팝업 닫기 완료")
    except Exception as e:
        logger.info("팝업이 없거나 닫기 실패: %s", e)
    try:
        await page.evaluate("document.querySelector('div[data-sentry-component=\"PopupAdvertise\"]').remove()")
        logger.info("팝업 요소 제거 완료")
    except Exception as e:
        logger.info("팝업 요소 제거 불필요: %s", e)
    try:
        await page.click("button:has-text('회원가입/로그인')", timeout=10000)
        logger.info("로그인 버튼 클릭 완료")
    except Exception as e:
        logger.info("로그인 버튼 클릭 실패: %s", e)
        await browser.close()
        return
    try:
        await page.wait_for_selector("input[name='id']", timeout=15000)
        logger.info("로그인 모달 로드 완료")
    except Exception as e:
        logger.info("로그인 모달 로드 실패: %s", e)
        await browser.close()
        return
    # --- 로그인 정보는 환경 변수나 다른 안전한 방법으로 관리하는 것을 권장합니다 ---
    # await page.fill("input[name='id']", "geuloing@gmail.com")
    # await page.fill("input[name='password']", "jssgpt564!")
    # --- 안전한 방법으로 대체 필요 ---
    login_id = os.getenv("JASOSEOL_ID") # 예시: 환경 변수 사용
    login_pw = os.getenv("JASOSEOL_PW") # 예시: 환경 변수 사용
    if not login_id or not login_pw:
         logger.error("로그인 ID 또는 PW 환경변수가 설정되지 않았습니다.")
         await browser.close()
         return
    await page.fill("input[name='id']", login_id)
    await page.fill("input[name='password']", login_pw)
    try:
        login_button = page.get_by_text("로그인", exact=True)
        await login_button.click(timeout=10000)
        logger.info("로그인 버튼 클릭 완료")
    except Exception as e:
        logger.info("로그인 버튼 클릭 실패: %s", e)
        await page.screenshot(path="error_screenshot_click_fail.png")
        await browser.close()
        return
    try:
        # 로그인 성공 후 나타나는 요소 대기 (텍스트나 URL 기반으로 변경 가능)
        await page.wait_for_selector("span.text-gray-900:has-text('의 맞춤공고예요.')", timeout=15000)
        logger.info("로그인 성공! 텍스트 확인 완료")
        # 성공 후 팝업 처리 추가
        try:
             await page.click("div[data-sentry-component='PopupAdvertise'] button", timeout=5000)
             logger.info("로그인 성공 후 팝업 닫기 완료")
        except Exception:
             logger.info("로그인 성공 후 팝업 없음 또는 닫기 실패")
    except Exception as e:
        logger.info("로그인 성공 텍스트 확인 실패: %s", e)
        current_url = page.url
        if "dashboard" in current_url:
            logger.info("로그인 성공 (URL 확인)!")
        else:
            await page.screenshot(path="error_screenshot_login_fail.png")
            logger.info("로그인 실패! 스크린샷 저장.")
            await browser.close()
            return
    await context.storage_state(path="state.json")
    logger.info("로그인 세션 저장 완료.")
    await browser.close()


async def extract_modal_data(page, calendar_item):
    # ... (extract_modal_data 함수 내용은 기존과 동일하게 유지) ...
    companies = []
    try:
        employment_items = await calendar_item.query_selector_all(".employment-group-item")
        if employment_items:
            for item in employment_items:
                label_elem = await item.query_selector("div.calendar-label.start")
                if label_elem:
                    label_text = (await label_elem.inner_text()).strip()
                    if label_text != "시":
                        continue
                link_elem = await item.query_selector("a.company")
                if link_elem:
                    href = await link_elem.get_attribute("href")
                    company_elem = await item.query_selector("div.company-name span")
                    company_name = await company_elem.inner_text() if company_elem else "N/A"
                    start_date = await calendar_item.get_attribute("day")
                    employment_id = await item.get_attribute("employment_id")
                    recruitment_title_elem = await item.query_selector(".employment-group-item__title-content.ng-binding")
                    recruitment_title = await recruitment_title_elem.inner_text() if recruitment_title_elem else f"{company_name} 채용 공고"
                    companies.append({
                        "start_date": start_date,
                        "end_date": None,
                        "employment_id": employment_id,
                        "link": "https://jasoseol.com" + href if href and href.startswith("/") else href,
                        "company_name": company_name,
                        "recruitment_title": recruitment_title,
                        "jobs": []
                    })
                    logger.info("모달 방식: 탐지된 기업 - %s", company_name)
                else:
                    logger.info("모달 방식: a.company 링크 없음. 그룹화된 항목 처리 시도.")
                    try:
                         await item.scroll_into_view_if_needed()
                         await item.click()
                         # 모달 로딩 대기 강화
                         await page.wait_for_selector(".employment-company-group-modal.in", state="visible", timeout=10000)
                         await page.wait_for_load_state("networkidle", timeout=5000) # 네트워크 안정화 추가

                         modal = await page.query_selector(".employment-company-group-modal")
                         if not modal:
                              logger.warning("모달 요소를 찾을 수 없습니다. 이 항목 건너뛰기.")
                              continue

                         modal_company_name = await modal.query_selector(".employment-group-title__content").inner_text()

                         # 그룹화된 항목 내 개별 공고 처리
                         modal_items = await modal.query_selector_all(".employment-group-item")
                         for modal_item in modal_items:
                              modal_link_elem = await modal_item.query_selector("a.employment-company-anchor")
                              modal_href = await modal_link_elem.get_attribute("href") if modal_link_elem else ""
                              modal_title_elem = await modal_item.query_selector(".employment-group-item__title-content")
                              modal_title = await modal_title_elem.inner_text() if modal_title_elem else f"{modal_company_name} 개별 공고"
                              modal_end_time_elem = await modal_item.query_selector(".employment-group-item__end-time")
                              modal_end_time = await modal_end_time_elem.inner_text() if modal_end_time_elem else None
                              modal_employment_id = await modal_item.get_attribute("employment_id")

                              companies.append({
                                   "start_date": await calendar_item.get_attribute("day"),
                                   "end_date": modal_end_time, # 개별 공고 마감일 사용
                                   "employment_id": modal_employment_id,
                                   "link": "https://jasoseol.com" + modal_href if modal_href and modal_href.startswith("/") else modal_href,
                                   "company_name": modal_company_name, # 그룹 대표 회사명
                                   "recruitment_title": modal_title, # 개별 공고 제목
                                   "jobs": []
                                })
                              logger.info(f"모달 내 개별 공고 탐지: {modal_company_name} - {modal_title}")

                         # 모달 닫기
                         close_button = await modal.query_selector("button.modal-close-btn")
                         if close_button:
                             await close_button.click()
                             await page.wait_for_selector(".employment-company-group-modal", state="hidden", timeout=5000)
                         else:
                             logger.warning("모달 닫기 버튼을 찾을 수 없어 강제 제거 시도.")
                             await page.evaluate("document.querySelector('.employment-company-group-modal').remove()")

                    except Exception as modal_detail_e:
                         logger.error(f"모달 세부 정보 처리 중 오류: {modal_detail_e}")
                         # 모달 닫기 시도 (오류 발생 시에도)
                         try:
                             if await page.query_selector(".employment-company-group-modal.in"):
                                 close_button = await page.query_selector(".employment-company-group-modal.in button.modal-close-btn")
                                 if close_button: await close_button.click(timeout=1000)
                                 else: await page.evaluate("document.querySelector('.employment-company-group-modal').remove()")
                         except:
                             logger.warning("오류 후 모달 닫기 실패")
                         continue # 오류 발생 시 다음 항목으로 이동
            return companies
        else:
            # 단일 항목 처리 로직 (기존과 유사하나, start 레이블 확인 추가)
            label_elem = await calendar_item.query_selector("div.calendar-label.start")
            if label_elem and (await label_elem.inner_text()).strip() == "시":
                 link_elem = await calendar_item.query_selector("a.company")
                 href = await link_elem.get_attribute("href") if link_elem else ""
                 start_date = await calendar_item.get_attribute("day")
                 employment_id = await calendar_item.get_attribute("employment_id")
                 company_elem = await calendar_item.query_selector("div.company-name span")
                 company_name = await company_elem.inner_text() if company_elem else "N/A"
                 recruitment_title = f"{company_name} 채용 공고"
                 single_company = {
                     "start_date": start_date,
                     "end_date": None, # 상세 페이지에서 가져와야 함
                     "employment_id": employment_id,
                     "link": "https://jasoseol.com" + href if href and href.startswith("/") else href,
                     "company_name": company_name,
                     "recruitment_title": recruitment_title,
                     "jobs": []
                 }
                 logger.info("모달 방식: 단일 기업 추출 - %s", company_name)
                 return [single_company]
            else:
                 logger.info("모달 방식: 단일 항목이지만 시작('시') 레이블이 아님. 건너뛰기.")
                 return []
    except Exception as e:
        logger.error("모달 추출 중 오류: %s", e)
        await page.screenshot(path="error_screenshot_modal_fail.png")
        return []


async def integrated_crawler(target_date, filter_company=None):
    # Keep the function yielding companies for compatibility with main()
    processed_companies = [] # List to collect companies before yielding

    async with async_playwright() as p:
        await ensure_logged_in(p)
        browser = await p.chromium.launch(
            headless=True, # 필요시 False로 변경하여 브라우저 확인
            args=["--disable-extensions", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            storage_state="state.json",
            viewport={"width": 1200, "height": 800} # 가시 영역 약간 넓게
        )
        page = await context.new_page()
        # 디버깅 시에는 리소스 차단을 일시적으로 해제해볼 수 있음
        # await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())
        logger.info("채용 공고 페이지로 이동 중...")
        try:
            await page.goto("https://jasoseol.com/recruit", wait_until='networkidle', timeout=60000) # 초기 로딩 대기 시간 증가
            logger.info("채용 공고 페이지 로드 완료.")
        except Exception as goto_e:
            logger.error(f"페이지 로드 실패: {goto_e}")
            await page.screenshot(path=f"debug_goto_fail_{target_date}.png")
            await browser.close()
            return

        try:
            # 팝업 처리 시도 (실패해도 계속 진행)
            logger.info("팝업 닫기 시도...")
            await page.click("div.popup-close", timeout=3000)
            logger.info("일반 팝업 닫기 완료.")
        except Exception:
            logger.info("일반 팝업 없음 또는 닫기 실패.")
        try:
            await page.click("div[data-sentry-component='PopupAdvertise'] button", timeout=3000)
            logger.info("광고 팝업 닫기 완료.")
        except Exception:
             logger.info("광고 팝업 없음 또는 닫기 실패.")

        logger.info("선택한 날짜: %s", target_date)

        calendar_items = [] # 초기화
        max_attempts = 12
        attempts = 0

        # 초기 날짜 검색
        try:
             logger.info("초기 날짜 항목 검색 시도...")
             await page.wait_for_selector("div.calendar-cell", timeout=15000) # 캘린더 셀 로딩 대기
             calendar_items = await page.query_selector_all(f"div.day-content[day='{target_date}'] > div.calendar-item") # 선택자 약간 수정 (day 속성은 day-content에 있음)
             logger.info(f"초기 검색 결과: {len(calendar_items)}개의 항목 발견 ({target_date}).")
        except Exception as e:
             logger.error(f"초기 캘린더 대기/검색 중 오류 발생: {e}")
             timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
             fail_html_path = f"debug_initial_calendar_fail_{target_date}_{timestamp}.html"
             await page.screenshot(path=f"debug_initial_calendar_fail_{target_date}_{timestamp}.png")
             try:
                 html_content = await page.content()
                 with open(fail_html_path, "w", encoding="utf-8") as f:
                     f.write(html_content)
                 logger.info(f"초기 캘린더 실패 시 HTML 저장: {fail_html_path}")
             except Exception as dump_e:
                 logger.error(f"초기 실패 HTML 저장 오류: {dump_e}")
             await browser.close()
             return

        # --- 월 이동 루프 ---
        while not calendar_items and attempts < max_attempts:
            logger.info(f"날짜 {target_date} 항목 없음. 다음 달로 이동 시도 ({attempts + 1}/{max_attempts})...")

            # 선택자 정의
            next_button_selector_primary = "div.calendar-nav img[ng-click='addMonth(1)']"
            next_button_selector_alt1 = "div.calendar-nav > div.icon-wrapper:nth-of-type(2) > img" # 두 번째 아이콘 래퍼
            current_month_display_selector = "div.calendar-nav > span.current"

            # 클릭 전 현재 월 확인
            current_month_text = "N/A"
            try:
                current_month_element = await page.query_selector(current_month_display_selector)
                if current_month_element:
                    current_month_text = await current_month_element.inner_text()
                logger.info(f"[디버깅] 현재 월 표시 (클릭 전): {current_month_text}")
            except Exception as e:
                 logger.warning(f"[디버깅] 현재 월 텍스트 가져오기 실패: {e}")

            # 다음 달 버튼 찾기
            next_button = None
            logger.info(f"[디버깅] 기본 선택자 시도: {next_button_selector_primary}")
            next_button = await page.query_selector(next_button_selector_primary)
            if not next_button:
                logger.warning(f"[디버깅] 기본 선택자 실패. 대체 선택자 1 시도: {next_button_selector_alt1}")
                next_button = await page.query_selector(next_button_selector_alt1)

            if not next_button:
                logger.error("[디버깅] 모든 선택자로 다음 달 버튼 찾기 실패.")
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                fail_html_path = f"debug_button_find_fail_{target_date}_attempt_{attempts}_{timestamp}.html"
                await page.screenshot(path=f"debug_button_find_fail_{target_date}_attempt_{attempts}_{timestamp}.png")
                try:
                    html_content = await page.content()
                    with open(fail_html_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.info(f"버튼 찾기 실패 시 HTML 저장: {fail_html_path}")
                except Exception as dump_e:
                    logger.error(f"버튼 실패 HTML 저장 오류: {dump_e}")
                break # 루프 종료

            # 버튼 클릭
            try:
                logger.info("[디버깅] 다음 달 버튼 클릭 중...")
                await next_button.click()
                logger.info("다음 달 버튼 클릭 성공.")
            except Exception as click_e:
                 logger.error(f"다음 달 버튼 클릭 오류: {click_e}")
                 await page.screenshot(path=f"debug_button_click_fail_{target_date}_attempt_{attempts}.png")
                 break # 클릭 실패 시 루프 종료

            # 월 변경 대기
            try:
                logger.info("[디버깅] 월 표시 변경 대기 중...")
                await page.wait_for_function(
                    f"""(selector, previous_text) => {{
                        const element = document.querySelector(selector);
                        // 요소가 있고, 텍스트가 있으며, 이전 텍스트와 다르고, 비어있지 않은지 확인
                        return element && element.innerText && element.innerText.trim() !== '' && element.innerText !== previous_text;
                    }}""",
                    (current_month_display_selector, current_month_text),
                    timeout=15000 # 대기 시간 15초
                )
                new_month_element = await page.query_selector(current_month_display_selector)
                new_month_text = await new_month_element.inner_text() if new_month_element else "N/A"
                logger.info(f"월 표시 변경됨: {new_month_text}. 항목 검색 시작...")
                await asyncio.sleep(1.5) # 렌더링을 위한 추가 대기 시간 (1.5초)

            except Exception as wait_e:
                logger.warning(f"월 표시 변경 대기 중 타임아웃 또는 오류 발생: {wait_e}")
                await page.screenshot(path=f"debug_wait_fail_{target_date}_attempt_{attempts}.png")
                logger.info("대기 실패했지만, 항목 검색 시도...")
                # break # 대기 실패 시 즉시 중단하려면 주석 해제

            # 날짜 항목 다시 검색
            try:
                 # 주의: day 속성은 div.day-content 에 있음. 그 안의 calendar-item 을 찾아야 함.
                 calendar_items = await page.query_selector_all(f"div.day-content[day='{target_date}'] > div.calendar-item")
                 logger.info(f"월 이동 후 검색 결과: {len(calendar_items)}개의 항목 발견 ({target_date}).")
            except Exception as search_e:
                 logger.error(f"월 이동 후 항목 검색 중 오류 발생: {search_e}")
                 break # 검색 오류 시 루프 종료

            attempts += 1
        # --- 월 이동 루프 종료 ---

        if not calendar_items:
            logger.warning(f"최종적으로 날짜 {target_date} 항목을 찾지 못했습니다 (시도 횟수: {attempts}).")
            if attempts == max_attempts:
                 timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                 fail_html_path = f"debug_final_loop_fail_{target_date}_{timestamp}.html"
                 await page.screenshot(path=f"debug_final_loop_fail_{target_date}_{timestamp}.png")
                 try:
                     html_content = await page.content()
                     with open(fail_html_path, "w", encoding="utf-8") as f:
                         f.write(html_content)
                     logger.info(f"최종 루프 실패 시 HTML 저장: {fail_html_path}")
                 except Exception as dump_e:
                     logger.error(f"최종 루프 실패 HTML 저장 오류: {dump_e}")
            await browser.close()
            return

        # --- 찾은 항목 처리 시작 ---
        logger.info(f"날짜 {target_date} 항목 {len(calendar_items)}개 처리 시작...")
        all_companies_data = [] # 모든 회사 데이터 수집용

        # calendar_items는 div.calendar-item 요소 리스트임
        for item_idx, item in enumerate(calendar_items):
             logger.info(f"항목 #{item_idx + 1} 처리 중...")
             parent_day_content = await item.query_selector("xpath=..") # 부모 day-content 요소 찾기
             current_item_day = await parent_day_content.get_attribute("day") if parent_day_content else target_date # 날짜 다시 확인

             companies_from_item = []
             # --- 항목 내 회사 정보 추출 로직 (기존 로직 재활용 및 개선) ---
             try:
                  # 그룹화된 항목인지 확인 (내부에 a.company가 없는 경우)
                  direct_link = await item.query_selector("a.company")
                  if direct_link and (await item.query_selector("div.calendar-label.start")): # 시작 '시' 레이블 확인
                       label_text = (await item.query_selector("div.calendar-label.start").inner_text()).strip()
                       if label_text == "시":
                            href = await direct_link.get_attribute("href")
                            company_elem = await item.query_selector("div.company-name span")
                            company_name = await company_elem.inner_text() if company_elem else "N/A"
                            employment_id = await item.get_attribute("employment_id")
                            recruitment_title = f"{company_name} 채용 공고"
                            companies_from_item.append({
                                "start_date": current_item_day, "end_date": None, "employment_id": employment_id,
                                "link": "https://jasoseol.com" + href if href and href.startswith("/") else href,
                                "company_name": company_name, "recruitment_title": recruitment_title, "jobs": []
                            })
                            logger.info(f"직접 링크 추출 성공: {company_name}")
                       else:
                            logger.info("직접 링크 있으나 시작('시') 레이블 아님. 건너뛰기.")
                  elif await item.query_selector(".company[period]"): # 그룹화된 항목 표시 확인 (.company div)
                       logger.info("그룹화된 항목 감지. 모달 추출 시도...")
                       companies_from_item = await extract_modal_data(page, item)
                       logger.info(f"모달 추출 결과: {len(companies_from_item)}개 회사")
                  else:
                       # 다른 유형의 항목 (예: '끝' 레이블만 있거나, 예상 못한 구조)
                       label_elem = await item.query_selector("div.calendar-label")
                       label_text = await label_elem.inner_text() if label_elem else "레이블 없음"
                       logger.info(f"처리할 수 없는 항목 유형 감지 (레이블: {label_text}). 건너뛰기.")
                       continue # 다음 항목으로

             except Exception as extract_e:
                  logger.error(f"항목 #{item_idx + 1} 처리 중 오류: {extract_e}")
                  continue # 오류 발생 시 다음 항목으로

             # --- 필터링 로직 (기존과 동일) ---
             if filter_company:
                 original_count = len(companies_from_item)
                 if isinstance(filter_company, list):
                     companies_from_item = [
                         company for company in companies_from_item
                         if any(name.lower() in company.get("company_name", "").lower() for name in filter_company)
                     ]
                 else:
                     companies_from_item = [
                         company for company in companies_from_item
                         if filter_company.lower() in company.get("company_name", "").lower()
                     ]
                 if len(companies_from_item) < original_count:
                      logger.info(f"필터링 적용: {original_count}개 -> {len(companies_from_item)}개")
                 if not companies_from_item:
                     logger.info(f"항목 #{item_idx+1}에서 필터 조건에 맞는 기업 없음. 건너뛰기.")
                     continue
             # --- 필터링 로직 끝 ---

             # --- 상세 정보 처리 로직 ---
             for company_data in companies_from_item:
                logger.info(f"상세 정보 처리 시작: {company_data.get('company_name')} (Link: {company_data.get('link')})")
                if not company_data.get('link'):
                    logger.warning(f"상세 정보 링크 없음: {company_data.get('company_name')}. 건너뛰기.")
                    continue

                detail_page = None # 초기화
                try:
                    # <<< --- 여기에 기존 상세 페이지 처리 로직 삽입 --- >>>
                    # 예시: detail_page 열고, 정보 추출 (end_date, recruitment_link, jobs...)
                    detail_page = await context.new_page()
                    # 상세 페이지 리소스 차단 해제 고려 (필요시)
                    # await detail_page.route("**/*", lambda route: route.continue_())
                    await detail_page.goto(company_data["link"], wait_until='domcontentloaded', timeout=60000) # 상세 페이지 로딩 대기

                    # 종료일 추출 (기존 로직 사용)
                    try:
                        selector_end_date = r"div.flex.gap-\[4px\].mb-\[20px\].body5"
                        await detail_page.wait_for_selector(selector_end_date, timeout=10000)
                        date_div = await detail_page.query_selector(selector_end_date)
                        spans = await date_div.query_selector_all("span")
                        end_date = (await spans[2].inner_text()).strip() if len(spans) >= 4 else None
                        company_data["end_date"] = end_date
                        logger.info(f"종료일 추출: {end_date}")
                    except Exception as e:
                        logger.warning(f"종료일 추출 오류: {e}. 기존 값 유지.")

                    # 채용 사이트 링크 추출 (기존 로직 사용)
                    try:
                        link_elem = await detail_page.query_selector("a.flex-grow:has(button:has-text('채용 사이트'))")
                        recruitment_link = await link_elem.get_attribute("href") if link_elem else None
                        company_data["recruitment_link"] = recruitment_link
                        logger.info(f"채용 사이트 링크: {recruitment_link}")
                    except Exception as e:
                        logger.warning(f"채용 사이트 링크 추출 오류: {e}")

                    # 직무 정보 및 자소서 문항 추출 (기존 로직 사용)
                    jobs = []
                    try:
                         # ul.shadow2 또는 li.flex.justify-center 대기 및 선택
                         job_list_selector = "ul.shadow2 li.flex.justify-center, div.rounded-\\[6px\\].border-gray-200 > ul > li.flex.justify-center" # 두 가지 가능한 구조 고려
                         await detail_page.wait_for_selector(job_list_selector, timeout=10000)
                         job_elements = await detail_page.query_selector_all(job_list_selector)
                         logger.info(f"직무 요소 {len(job_elements)}개 발견.")

                         for job_idx, li_elem in enumerate(job_elements):
                             recruitment_type = recruitment_title = None
                             try:
                                 # 직무 타입/제목 추출 개선 (더 많은 span 구조 고려)
                                 title_span = await li_elem.query_selector("span.text-gray-900.body2, span.text-gray-900.body3_bold") # 가능한 제목 span
                                 type_span = await li_elem.query_selector("span.label1_bold.text-secondary-700") # 타입 span

                                 recruitment_title = await title_span.inner_text() if title_span else "N/A"
                                 recruitment_type = await type_span.inner_text() if type_span else None

                                 logger.info(f"  - 직무 #{job_idx+1}: {recruitment_title} (타입: {recruitment_type})")
                             except Exception as e:
                                 logger.warning(f"  - 직무 #{job_idx+1} 타입/제목 추출 오류: {e}")

                             essay_questions = []
                             try:
                                 # 자소서 버튼 대기 및 클릭
                                 essay_button_selector = "button:has-text('자기소개서 쓰기')"
                                 button = await li_elem.query_selector(essay_button_selector)
                                 if button:
                                     await button.scroll_into_view_if_needed()
                                     await button.click()
                                     await asyncio.sleep(0.5) # 클릭 후 잠시 대기

                                     # 자소서 문항 요소 대기 및 추출 (구조 변경 가능성 있음)
                                     essay_block_selector = "div.py-\\[20px\\].px-\\[16px\\] div.font-normal.mb-\\[8px\\]" # 좀 더 구체적인 경로
                                     await li_elem.wait_for_selector(essay_block_selector, timeout=5000)
                                     essay_blocks = await li_elem.query_selector_all(essay_block_selector)

                                     logger.info(f"    자소서 블록 {len(essay_blocks)}개 발견.")
                                     for block in essay_blocks:
                                         # question/limit 추출 로직 개선 (텍스트 클래스 확인 필요)
                                         q_elem = await block.query_selector("div.text-\\[14px\\], div.text-gray-900.body4") # 가능한 질문 selector
                                         l_elem = await block.query_selector("div.text-\\[10px\\], div.text-gray-500.caption1") # 가능한 제한 selector
                                         if q_elem and l_elem:
                                             q_text = (await q_elem.inner_text()).strip()
                                             l_text = (await l_elem.inner_text()).strip()
                                             essay_questions.append({"question": q_text,"limit": l_text})
                                             logger.info(f"      질문: {q_text[:30]}... (제한: {l_text})")
                                         else:
                                             logger.warning("      질문 또는 제한 요소를 찾을 수 없음.")
                                 else:
                                     logger.info("    '자기소개서 쓰기' 버튼 없음.")
                             except Exception as e:
                                 # TimeoutError는 흔할 수 있으므로 warning 처리
                                 if "Timeout" in str(e):
                                      logger.warning(f"    자소서 문항 추출 중 타임아웃 또는 오류: {e}")
                                 else:
                                      logger.error(f"    자소서 문항 추출 중 오류: {e}", exc_info=True)


                             jobs.append({
                                 "recruitment_type": recruitment_type,
                                 "recruitment_title": recruitment_title,
                                 "essay_questions": essay_questions
                             })
                         company_data["jobs"] = jobs
                    except Exception as e:
                         logger.warning(f"직무 정보 추출 중 오류 발생: {e}")
                         # 직무 정보가 없어도 회사 정보는 저장할 수 있도록 처리

                    # <<< --- 기존 상세 페이지 처리 로직 끝 --- >>>

                    all_companies_data.append(company_data) # 성공적으로 처리된 회사 데이터 추가
                    logger.info(f"상세 정보 처리 완료: {company_data.get('company_name')}")

                except Exception as detail_e:
                     logger.error(f"상세 정보 처리 중 예외 발생: {company_data.get('company_name')} ({company_data.get('link')}) - {detail_e}", exc_info=True) # 상세 에러 출력
                     await page.screenshot(path=f"debug_detail_fail_{company_data.get('company_name')}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png")
                     # 오류 발생 시 해당 회사 건너뛰기
                     continue
                finally:
                     if detail_page and not detail_page.is_closed():
                          await detail_page.close() # 페이지 확실히 닫기

        await browser.close()
        logger.info(f"날짜 {target_date} 처리 완료. 총 {len(all_companies_data)}개 회사 데이터 반환.")

        # 처리된 모든 회사 데이터를 yield
        for company in all_companies_data:
            yield company

async def main(target_date, filter_company=None):
    # integrated_crawler가 generator이므로 이 구조는 그대로 작동합니다.
    async for company in integrated_crawler(target_date, filter_company):
        yield company

if __name__ == "__main__":
    target_date = input("크롤링할 날짜 (YYYYMMDD)를 입력하세요: ")
    company_name = input("기업명 (선택, 여러 개는 쉼표로 구분, 없으면 엔터): ").strip() or None
    if company_name:
        company_names = [name.strip() for name in company_name.split(",") if name.strip()]
    else:
        company_names = None
    companies_data = []
    async def collect_data():
        async for company in main(target_date, company_names):
            companies_data.append(company)
            # 실시간 출력을 원하면 여기서 print 가능
            # print(json.dumps(company, ensure_ascii=False, indent=2))
    asyncio.run(collect_data())
    # 최종 결과 출력 (필요시)
    print(f"\n--- 최종 수집된 데이터 ({len(companies_data)}개) ---")
    print(json.dumps(companies_data, ensure_ascii=False, indent=2))