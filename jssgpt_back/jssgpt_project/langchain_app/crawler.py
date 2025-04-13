# crawler.py

import sys
import asyncio
import json
import logging
import os
import datetime # datetime 모듈 추가
from playwright.async_api import async_playwright

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ensure_logged_in 함수 ---
async def ensure_logged_in(playwright):
    # (사용자가 제공한 코드 내용과 동일하게 유지)
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

    # --- 로그인 정보는 환경 변수나 다른 안전한 방법으로 관리 권장 ---
    # login_id = os.getenv("JASOSEOL_ID", "geuloing@gmail.com") # 기본값 또는 환경 변수
    # login_pw = os.getenv("JASOSEOL_PW", "jssgpt564!") # 기본값 또는 환경 변수
    # 사용자가 제공한 코드 대로 유지:
    login_id = "geuloing@gmail.com"
    login_pw = "jssgpt564!"
    # --- 로그인 정보 끝 ---

    if not login_id or not login_pw:
         logger.error("로그인 ID 또는 PW를 설정해야 합니다.")
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
        await page.wait_for_selector("span.text-gray-900:has-text('의 맞춤공고예요.')", timeout=15000)
        logger.info("로그인 성공! 텍스트 확인 완료")
        try: # 로그인 후 팝업 처리
             await page.click("div[data-sentry-component='PopupAdvertise'] button", timeout=5000)
             logger.info("로그인 성공 후 팝업 닫기 완료")
        except Exception:
             logger.info("로그인 성공 후 팝업 없음 또는 닫기 실패")
    except Exception as e:
        logger.info("로그인 성공 텍스트 확인 실패: %s", e)
        current_url = page.url
        if "dashboard" in current_url: logger.info("로그인 성공 (URL 확인)!")
        else:
            await page.screenshot(path="error_screenshot_login_fail.png"); logger.info("로그인 실패! 스크린샷 저장.")
            await browser.close(); return
    await context.storage_state(path="state.json")
    logger.info("로그인 세션 저장 완료.")
    await browser.close()


# --- extract_modal_data 함수 ---
async def extract_modal_data(page, calendar_item):
    # (사용자가 제공한 코드 내용과 동일하게 유지)
    companies = []
    try:
        # 그룹 아이템 내부의 개별 항목들을 찾음
        modal_items = await calendar_item.query_selector_all(".employment-group-item")
        is_group_trigger = False # 모달을 직접 클릭해야 하는지 여부

        # 모달을 클릭해야 하는지 판단 (직접적인 .employment-group-item 이 없는 경우)
        if not modal_items and await calendar_item.query_selector(".company[period]"):
            logger.info("[Modal] 그룹화된 항목 감지. 모달 클릭 필요.")
            is_group_trigger = True
            # 모달 트리거 클릭
            await calendar_item.scroll_into_view_if_needed()
            await calendar_item.click()
            await page.wait_for_selector(".employment-company-group-modal.in", state="visible", timeout=10000)
            await page.wait_for_load_state("networkidle", timeout=5000)
            modal = await page.query_selector(".employment-company-group-modal.in")
            if not modal: raise Exception("모달 요소를 찾을 수 없음")
            modal_items = await modal.query_selector_all(".employment-group-item") # 모달 내에서 항목 다시 찾기
            logger.info(f"[Modal] 클릭 후 모달 내 {len(modal_items)}개 항목 발견.")
        elif not modal_items: # 그룹 아이템도 아니고, 내부 항목도 없으면 처리 불가
             logger.info("[Modal] employment-group-item 없음. 단일 항목 처리 시도.")
             modal_items = [calendar_item] # 자기 자신을 항목으로 간주

        # 각 항목(모달 내 또는 직접) 처리
        for item in modal_items:
            link_elem = await item.query_selector("a.company, a.employment-company-anchor") # 가능한 링크 요소
            company_name_elem = await item.query_selector("div.company-name span")
            group_title_elem = await page.query_selector(".employment-company-group-modal.in .employment-group-title__content") # 모달 제목

            company_name = "N/A"
            href = None
            employment_id = None
            start_date = await calendar_item.get_attribute("day") # 시작일은 원래 calendar_item 기준

            if company_name_elem: # 항목 자체에 이름이 있으면 사용
                 company_name = (await company_name_elem.inner_text()).strip()
            elif group_title_elem and is_group_trigger: # 모달 제목 사용 (모달 클릭한 경우)
                 company_name = (await group_title_elem.inner_text()).strip()

            if link_elem:
                 href = await link_elem.get_attribute("href")
                 employment_id = await item.get_attribute("employment_id")

            # 레이블 확인 ('시'가 아니면 건너뛰기 - 사용자의 원본 코드 로직 유지)
            label_elem = await item.query_selector("div.calendar-label.start")
            if label_elem:
                 label_text = (await label_elem.inner_text()).strip()
                 if label_text != "시":
                      logger.info(f"[Modal] '{company_name}' 항목 레이블 '시' 아님 ({label_text}). 건너뛰기.")
                      continue # '시' 레이블 아니면 처리 안 함
            elif not is_group_trigger: # 그룹 트리거 아닌데 시작 레이블 없으면 건너뛰기 (단일 항목 처리 시)
                 logger.info(f"[Modal] '{company_name}' 단일 항목 시작 레이블 없음. 건너뛰기.")
                 continue

            if company_name != "N/A" and href:
                recruitment_title_elem = await item.query_selector(".employment-group-item__title-content")
                recruitment_title = await recruitment_title_elem.inner_text() if recruitment_title_elem else f"{company_name} 채용 공고"
                companies.append({
                    "start_date": start_date, "end_date": None, "employment_id": employment_id,
                    "link": "https://jasoseol.com" + href if href and href.startswith("/") else href,
                    "company_name": company_name, "recruitment_title": recruitment_title, "jobs": []
                })
                logger.info(f"[Modal] 처리 완료: {company_name} - {recruitment_title}")

        # 모달 닫기 (모달을 열었을 경우)
        if is_group_trigger:
            try:
                close_button = await page.query_selector(".employment-company-group-modal.in button.modal-close-btn")
                if close_button: await close_button.click(); await page.wait_for_selector(".employment-company-group-modal", state="hidden", timeout=5000)
                else: await page.evaluate("document.querySelector('.employment-company-group-modal.in')?.remove()")
            except Exception as close_e: logger.warning(f"모달 닫기 중 오류: {close_e}")

    except Exception as e:
        logger.error(f"모달 추출 중 오류: {e}")
        # 오류 발생 시에도 모달 닫기 시도
        try:
            if await page.query_selector(".employment-company-group-modal.in"):
                await page.evaluate("document.querySelector('.employment-company-group-modal.in button.modal-close-btn')?.click()")
                await asyncio.sleep(0.5)
                if await page.query_selector(".employment-company-group-modal.in"):
                     await page.evaluate("document.querySelector('.employment-company-group-modal.in')?.remove()")
        except: pass
    return companies


# --- [신규] 특정 날짜의 회사 기본 정보 찾는 헬퍼 함수 ---
async def find_companies_on_date(page, search_date_str, company_filter):
    """지정된 날짜에서 필터 조건에 맞는 회사의 기본 정보를 찾아 리스트로 반환"""
    matching_companies_basic_info = []
    try:
        day_content_selector = f"div.day-content[day='{search_date_str}']"
        logger.info(f"[Helper] 날짜 {search_date_str}의 '{day_content_selector}' 검색 시도...")
        await page.wait_for_selector(day_content_selector, timeout=15000)
        logger.info(f"[Helper] 날짜 {search_date_str}의 div.day-content 발견됨.")

        items_on_date = await page.query_selector_all(f"{day_content_selector} > div.calendar-item")
        logger.info(f"[Helper] 날짜 {search_date_str} 에서 {len(items_on_date)}개의 항목 발견.")

        if not items_on_date: return []

        for item_idx, item in enumerate(items_on_date):
            company_name = None
            href = None
            employment_id = None
            basic_info_list = []

            try:
                link_elem = await item.query_selector("a.company")
                company_name_elem = await item.query_selector("div.company-name span")
                group_div_elem = await item.query_selector("div.company[period]") # 그룹 div 확인

                # '시' 레이블 확인 (사용자 원본 코드 로직 반영)
                label_elem = await item.query_selector("div.calendar-label.start")
                is_start_label = False
                if label_elem:
                    label_text = (await label_elem.inner_text()).strip()
                    if label_text == "시":
                        is_start_label = True

                if link_elem and company_name_elem and is_start_label: # 직접 링크 + '시' 레이블
                    company_name = (await company_name_elem.inner_text()).strip()
                    href = await link_elem.get_attribute("href")
                    employment_id = await item.get_attribute("employment_id")
                    basic_info_list.append({
                        "start_date": search_date_str, "end_date": None, "employment_id": employment_id,
                        "link": "https://jasoseol.com" + href if href and href.startswith("/") else href,
                        "company_name": company_name,
                        "recruitment_title": f"{company_name} 채용 공고", "jobs": []
                    })
                    logger.info(f"[Helper] 직접 링크 항목 처리: {company_name}")
                elif group_div_elem: # 그룹 (모달) - '시' 레이블 없어도 모달은 시도
                    logger.info(f"[Helper] 그룹 항목 발견 (항목 #{item_idx+1}). 모달 추출 시도...")
                    basic_info_list = await extract_modal_data(page, item) # 모달 처리 함수 호출
                else:
                    logger.debug(f"[Helper] 직접 링크+시작 레이블 조건 미충족 및 그룹 항목 아님 (항목 #{item_idx+1}).")


            except Exception as extract_e:
                logger.warning(f"[Helper] 항목 #{item_idx + 1} 기본 정보 추출 오류: {extract_e}")
                continue

            # 필터링
            for basic_info in basic_info_list:
                 process_this = True
                 current_comp_name = basic_info.get("company_name")
                 if company_filter and current_comp_name:
                     target_names_lower = [name.lower().strip() for name in company_filter] if isinstance(company_filter, list) else [company_filter.lower().strip()]
                     if not any(target_name in current_comp_name.lower().strip() for target_name in target_names_lower):
                         process_this = False
                 elif not current_comp_name:
                     process_this = False

                 if process_this:
                     logger.info(f"[Helper] 필터 통과: '{current_comp_name}' (날짜: {search_date_str})")
                     matching_companies_basic_info.append(basic_info)

    except Exception as e:
        if "Timeout" in str(e): logger.warning(f"[Helper] 날짜 {search_date_str} 검색/대기 타임아웃.")
        else: logger.error(f"[Helper] 날짜 {search_date_str} 처리 중 오류: {e}")
        return []

    return matching_companies_basic_info
# --- 헬퍼 함수 끝 ---


# --- 메인 크롤러 함수 ---
async def integrated_crawler(target_date, filter_company=None):
    processed_companies_yielded = set() # 중복 yield 방지용

    async with async_playwright() as p:
        await ensure_logged_in(p)
        browser = await p.chromium.launch(
            headless=True, args=["--disable-extensions", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        # 리소스 최적화를 위해 UserAgent 설정 고려
        context = await browser.new_context(
             storage_state="state.json",
             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36", # 일반적인 UserAgent
             viewport={"width": 1200, "height": 800}
        )
        page = await context.new_page()
        # 네트워크 요청 최적화 (폰트/이미지/미디어 차단)
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font", "stylesheet"] else route.continue_())


        logger.info("채용 공고 페이지로 이동 중...")
        try:
            await page.goto("https://jasoseol.com/recruit", wait_until='domcontentloaded', timeout=60000) # DOM 로드 우선
            logger.info("페이지 DOM 로드 완료. 네트워크 안정화 대기...")
            await page.wait_for_load_state('networkidle', timeout=30000) # 네트워크 안정화 추가 대기
            logger.info("채용 공고 페이지 로드 및 안정화 완료.")
            try: # 팝업 처리
                 await page.click("div.popup-close, div[data-sentry-component='PopupAdvertise'] button", timeout=5000)
            except: logger.info("팝업 닫기 실패 또는 없음")
        except Exception as goto_e:
            logger.error(f"페이지 로드 실패: {goto_e}")
            await page.screenshot(path=f"debug_goto_fail_{target_date}.png")
            await browser.close(); return

        # 1. --- 지정된 날짜(target_date) 검색 ---
        logger.info(f"--- 지정 날짜 검색 시작: {target_date} ---")
        target_date_companies = await find_companies_on_date(page, target_date, filter_company)

        # 상세 정보 처리 및 Yield (1차)
        for company_data in target_date_companies:
            company_key = f"{company_data.get('company_name','N/A').lower().strip()}_{company_data.get('employment_id', '')}"
            if company_key in processed_companies_yielded: continue

            detail_page = None
            try:
                logger.info(f"  상세 정보 처리: {company_data.get('company_name')} (날짜: {target_date})")

                # --- 상세 정보 처리 로직 시작 ---
                detail_page = await context.new_page()
                # 상세 페이지 리소스 차단 (선택적)
                await detail_page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font", "stylesheet"] else route.continue_())

                try:
                    await detail_page.goto(company_data["link"], wait_until='domcontentloaded', timeout=60000) # 상세 페이지 DOM 로드
                    await detail_page.wait_for_load_state('networkidle', timeout=20000) # 상세 페이지 네트워크 안정화
                except Exception as detail_goto_e:
                     logger.error(f"    상세 페이지({company_data['link']}) 로드 실패: {detail_goto_e}")
                     await detail_page.close()
                     continue # 다음 회사로

                # 상세 페이지 팝업 처리 (필요시)
                try: await detail_page.click("div.popup-close, div[data-sentry-component='PopupAdvertise'] button", timeout=3000)
                except: logger.info("    상세 페이지 팝업 없음 또는 닫기 실패")

                # 종료일 추출
                try:
                    selector_end_date = r"div.flex.gap-\[4px\].mb-\[20px\].body5" # Tailwind 클래스 특수문자 escape
                    await detail_page.wait_for_selector(selector_end_date, timeout=10000)
                    date_div = await detail_page.query_selector(selector_end_date)
                    spans = await date_div.query_selector_all("span")
                    end_date = (await spans[2].inner_text()).strip() if len(spans) >= 4 else None
                    company_data["end_date"] = end_date
                    logger.info(f"    종료일 추출: {end_date}")
                except Exception as e: logger.warning(f"    종료일 추출 오류: {e}")

                # 채용 사이트 링크 추출
                try:
                    link_elem = await detail_page.query_selector("a.flex-grow:has(button:has-text('채용 사이트'))")
                    recruitment_link = await link_elem.get_attribute("href") if link_elem else None
                    company_data["recruitment_link"] = recruitment_link
                    logger.info(f"    채용 사이트 링크: {recruitment_link}")
                except Exception as e: logger.warning(f"    채용 사이트 링크 추출 오류: {e}")

                # 직무/자소서 추출
                jobs = []
                try:
                    # 가능한 직무 목록 컨테이너 선택자들
                    job_list_selectors = [
                        "ul.shadow2", # 기존 선택자
                        "div.rounded-\\[6px\\].border-gray-200 > ul" # 다른 가능한 구조
                    ]
                    job_container = None
                    for sel in job_list_selectors:
                         container = await detail_page.query_selector(sel)
                         if container:
                              job_container = container
                              logger.info(f"    직무 컨테이너 찾음: {sel}")
                              break
                    if not job_container: raise Exception("직무 컨테이너 요소를 찾을 수 없음")

                    # 직무 항목 선택자
                    job_item_selector = "li.flex.justify-center"
                    await job_container.wait_for_selector(job_item_selector, timeout=10000) # 항목 로딩 대기
                    job_elements = await job_container.query_selector_all(job_item_selector)
                    logger.info(f"    직무 요소 {len(job_elements)}개 발견.")

                    for job_idx, li_elem in enumerate(job_elements):
                          recruitment_type = recruitment_title = None
                          try:
                              # 직무 타입/제목 추출 (가능한 여러 클래스 고려)
                              title_span = await li_elem.query_selector("span.text-gray-900.body2, span.text-gray-900.body3_bold")
                              type_span = await li_elem.query_selector("span.label1_bold.text-secondary-700")
                              recruitment_title = await title_span.inner_text() if title_span else "N/A"
                              recruitment_type = await type_span.inner_text() if type_span else None
                              logger.info(f"      직무 #{job_idx+1}: {recruitment_title} (타입: {recruitment_type})")
                          except Exception as e: logger.warning(f"      직무 #{job_idx+1} 타입/제목 추출 오류: {e}")

                          essay_questions = []
                          try:
                              # 자소서 버튼 클릭 및 문항 추출
                              essay_button_selector = "button:has-text('자기소개서 쓰기')"
                              button = await li_elem.query_selector(essay_button_selector)
                              if button:
                                  await button.scroll_into_view_if_needed(); await button.click(); await asyncio.sleep(0.5)
                                  # 문항 블록 선택자 (더 구체적)
                                  essay_block_selector = "div.py-\\[20px\\].px-\\[16px\\] div.font-normal.mb-\\[8px\\]"
                                  await li_elem.wait_for_selector(essay_block_selector, timeout=5000)
                                  essay_blocks = await li_elem.query_selector_all(essay_block_selector)
                                  logger.info(f"        자소서 블록 {len(essay_blocks)}개 발견.")
                                  for block_idx, block in enumerate(essay_blocks):
                                      # 질문/제한 선택자 (여러 가능성)
                                      q_elem = await block.query_selector("div.text-\\[14px\\], div.text-gray-900.body4")
                                      l_elem = await block.query_selector("div.text-\\[10px\\], div.text-gray-500.caption1")
                                      if q_elem and l_elem:
                                          q_text = (await q_elem.inner_text()).strip(); l_text = (await l_elem.inner_text()).strip()
                                          essay_questions.append({"question": q_text,"limit": l_text})
                                          logger.info(f"          질문 #{block_idx+1}: {q_text[:20]}... ({l_text})")
                                      else: logger.warning(f"        질문/제한 요소 못찾음 (블록 #{block_idx+1})")
                              else: logger.info("        '자기소개서 쓰기' 버튼 없음.")
                          except Exception as e:
                              if "Timeout" in str(e): logger.warning(f"      자소서 문항 추출 타임아웃: {e}")
                              else: logger.error(f"      자소서 문항 추출 오류: {e}", exc_info=False)
                          jobs.append({"recruitment_type": recruitment_type, "recruitment_title": recruitment_title, "essay_questions": essay_questions})
                    company_data["jobs"] = jobs
                except Exception as e:
                     logger.warning(f"    직무 정보 추출 중 오류 발생: {e}")
                # --- 상세 정보 처리 로직 끝 ---

                processed_companies_yielded.add(company_key) # 처리 완료 표시
                yield company_data # 결과 반환

            except Exception as detail_e:
                logger.error(f"  상세 정보 처리 오류 ({company_data.get('company_name')}): {detail_e}", exc_info=True)
            finally:
                if detail_page and not detail_page.is_closed(): await detail_page.close()


        # 2. --- 전날(previous_date) 검색 (필터가 있고, 지정 날짜에서 못 찾았을 경우) ---
        target_company_found = False
        if filter_company:
            filter_names_lower = {name.lower().strip() for name in filter_company} if isinstance(filter_company, list) else {filter_company.lower().strip()}
            processed_names_lower = {name_key.split('_')[0] for name_key in processed_companies_yielded}
            if any(name in processed_names_lower for name in filter_names_lower):
                target_company_found = True

        if filter_company and not target_company_found:
            logger.info(f"지정 날짜({target_date})에서 {filter_company} 못 찾음. 전날 검색 시도.")
            try:
                current_dt = datetime.datetime.strptime(target_date, "%Y%m%d")
                previous_dt = current_dt - datetime.timedelta(days=1)
                previous_date_str = previous_dt.strftime("%Y%m%d")

                # --- [필요시] 이전 달 이동 로직 ---
                current_month_display_selector = "div.calendar-nav > span.current"
                current_month_element = await page.query_selector(current_month_display_selector)
                current_month_text = await current_month_element.inner_text() if current_month_element else ""
                target_prev_month_text = previous_dt.strftime("%Y.%m")

                if current_month_text and target_prev_month_text < current_month_text.replace(".",""):
                    logger.info(f"현재 월({current_month_text}) -> 이전 달({target_prev_month_text}) 이동 시도...")
                    prev_button_selector = "div.calendar-nav img[ng-click='addMonth(-1)']"
                    prev_button = await page.query_selector(prev_button_selector)
                    if prev_button:
                        await prev_button.click()
                        await page.wait_for_function( # 월 변경 대기
                           f"""(selector, previous_text) => {{
                                const element = document.querySelector(selector);
                                return element && element.innerText && element.innerText.trim() !== '' && element.innerText !== previous_text;
                           }}""",
                           (current_month_display_selector, current_month_text), timeout=15000
                        )
                        await asyncio.sleep(1.5)
                        logger.info(f"이전 달({target_prev_month_text})로 이동 완료.")
                    else: logger.error("이전 달 버튼을 찾을 수 없음!")
                # --- 이전 달 이동 로직 끝 ---

                logger.info(f"--- 전날 검색 시작: {previous_date_str} ---")
                previous_date_companies = await find_companies_on_date(page, previous_date_str, filter_company)

                # 상세 정보 처리 및 Yield (2차)
                for company_data in previous_date_companies:
                    company_key = f"{company_data.get('company_name','N/A').lower().strip()}_{company_data.get('employment_id', '')}"
                    if company_key in processed_companies_yielded: continue

                    detail_page = None
                    try:
                        logger.info(f"  상세 정보 처리: {company_data.get('company_name')} (날짜: {previous_date_str})")

                        # --- 상세 정보 처리 로직 시작 ---
                        detail_page = await context.new_page()
                        await detail_page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font", "stylesheet"] else route.continue_())
                        try:
                            await detail_page.goto(company_data["link"], wait_until='domcontentloaded', timeout=60000)
                            await detail_page.wait_for_load_state('networkidle', timeout=20000)
                        except Exception as detail_goto_e:
                             logger.error(f"    상세 페이지({company_data['link']}) 로드 실패: {detail_goto_e}")
                             await detail_page.close(); continue

                        try: await detail_page.click("div.popup-close, div[data-sentry-component='PopupAdvertise'] button", timeout=3000)
                        except: logger.info("    상세 페이지 팝업 없음 또는 닫기 실패")

                        # 종료일 추출
                        try:
                            selector_end_date = r"div.flex.gap-\[4px\].mb-\[20px\].body5"
                            await detail_page.wait_for_selector(selector_end_date, timeout=10000)
                            date_div = await detail_page.query_selector(selector_end_date)
                            spans = await date_div.query_selector_all("span")
                            end_date = (await spans[2].inner_text()).strip() if len(spans) >= 4 else None
                            company_data["end_date"] = end_date
                            logger.info(f"    종료일 추출: {end_date}")
                        except Exception as e: logger.warning(f"    종료일 추출 오류: {e}")

                        # 채용 사이트 링크 추출
                        try:
                            link_elem = await detail_page.query_selector("a.flex-grow:has(button:has-text('채용 사이트'))")
                            recruitment_link = await link_elem.get_attribute("href") if link_elem else None
                            company_data["recruitment_link"] = recruitment_link
                            logger.info(f"    채용 사이트 링크: {recruitment_link}")
                        except Exception as e: logger.warning(f"    채용 사이트 링크 추출 오류: {e}")

                        # 직무/자소서 추출
                        jobs = []
                        try:
                            job_list_selectors = ["ul.shadow2", "div.rounded-\\[6px\\].border-gray-200 > ul"]
                            job_container = None
                            for sel in job_list_selectors:
                                container = await detail_page.query_selector(sel)
                                if container: job_container = container; logger.info(f"    직무 컨테이너 찾음: {sel}"); break
                            if not job_container: raise Exception("직무 컨테이너 요소를 찾을 수 없음")

                            job_item_selector = "li.flex.justify-center"
                            await job_container.wait_for_selector(job_item_selector, timeout=10000)
                            job_elements = await job_container.query_selector_all(job_item_selector)
                            logger.info(f"    직무 요소 {len(job_elements)}개 발견.")

                            for job_idx, li_elem in enumerate(job_elements):
                                  recruitment_type = recruitment_title = None
                                  try:
                                      title_span = await li_elem.query_selector("span.text-gray-900.body2, span.text-gray-900.body3_bold")
                                      type_span = await li_elem.query_selector("span.label1_bold.text-secondary-700")
                                      recruitment_title = await title_span.inner_text() if title_span else "N/A"
                                      recruitment_type = await type_span.inner_text() if type_span else None
                                      logger.info(f"      직무 #{job_idx+1}: {recruitment_title} (타입: {recruitment_type})")
                                  except Exception as e: logger.warning(f"      직무 #{job_idx+1} 타입/제목 추출 오류: {e}")

                                  essay_questions = []
                                  try:
                                      essay_button_selector = "button:has-text('자기소개서 쓰기')"
                                      button = await li_elem.query_selector(essay_button_selector)
                                      if button:
                                          await button.scroll_into_view_if_needed(); await button.click(); await asyncio.sleep(0.5)
                                          essay_block_selector = "div.py-\\[20px\\].px-\\[16px\\] div.font-normal.mb-\\[8px\\]"
                                          await li_elem.wait_for_selector(essay_block_selector, timeout=5000)
                                          essay_blocks = await li_elem.query_selector_all(essay_block_selector)
                                          logger.info(f"        자소서 블록 {len(essay_blocks)}개 발견.")
                                          for block_idx, block in enumerate(essay_blocks):
                                              q_elem = await block.query_selector("div.text-\\[14px\\], div.text-gray-900.body4")
                                              l_elem = await block.query_selector("div.text-\\[10px\\], div.text-gray-500.caption1")
                                              if q_elem and l_elem:
                                                  q_text = (await q_elem.inner_text()).strip(); l_text = (await l_elem.inner_text()).strip()
                                                  essay_questions.append({"question": q_text,"limit": l_text})
                                                  logger.info(f"          질문 #{block_idx+1}: {q_text[:20]}... ({l_text})")
                                              else: logger.warning(f"        질문/제한 요소 못찾음 (블록 #{block_idx+1})")
                                      else: logger.info("        '자기소개서 쓰기' 버튼 없음.")
                                  except Exception as e:
                                      if "Timeout" in str(e): logger.warning(f"      자소서 문항 추출 타임아웃: {e}")
                                      else: logger.error(f"      자소서 문항 추출 오류: {e}", exc_info=False)
                                  jobs.append({"recruitment_type": recruitment_type, "recruitment_title": recruitment_title, "essay_questions": essay_questions})
                            company_data["jobs"] = jobs
                        except Exception as e:
                             logger.warning(f"    직무 정보 추출 중 오류 발생: {e}")
                        # --- 상세 정보 처리 로직 끝 ---

                        processed_companies_yielded.add(company_key)
                        yield company_data # 결과 반환
                    except Exception as detail_e:
                        logger.error(f"  상세 정보 처리 오류 ({company_data.get('company_name')}): {detail_e}", exc_info=True)
                    finally:
                        if detail_page and not detail_page.is_closed(): await detail_page.close()

            except Exception as fallback_e:
                logger.error(f"전날 검색 중 오류 발생: {fallback_e}")

        # --- 브라우저 닫기 ---
        await browser.close()
        logger.info("크롤러 작업 완료.")


# --- main 함수 및 if __name__ == "__main__": 블록 ---
async def main(target_date, filter_company=None):
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
    asyncio.run(collect_data())
    print(f"\n--- 최종 수집된 데이터 ({len(companies_data)}개) ---")
    print(json.dumps(companies_data, ensure_ascii=False, indent=2))