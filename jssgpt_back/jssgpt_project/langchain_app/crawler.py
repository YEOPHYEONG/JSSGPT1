import sys
import asyncio
import json
import logging
import os
from playwright.async_api import async_playwright

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

async def ensure_logged_in(playwright):
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
    await page.fill("input[name='id']", "geuloing@gmail.com")
    await page.fill("input[name='password']", "jssgpt564!")
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
        await page.wait_for_selector("div[data-sentry-component='PopupAdvertise']", timeout=15000)
        logger.info("로그인 성공 후 팝업 감지!")
        await page.click("div[data-sentry-component='PopupAdvertise'] button", timeout=5000)
        logger.info("로그인 성공 후 팝업 닫기 완료")
    except Exception as e:
        logger.info("팝업 감지 실패. 텍스트 또는 URL로 로그인 확인 진행: %s", e)
        try:
            await page.wait_for_selector("span.text-gray-900:has-text('의 맞춤공고예요.')", timeout=15000)
            logger.info("로그인 성공! 텍스트 확인 완료")
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
                    logger.info("모달 방식: a.company 링크 없음. 추가 처리 필요.")
                    await item.scroll_into_view_if_needed()
                    await item.click()
                    await page.wait_for_selector(".employment-company-group-modal.in", state="visible", timeout=10000)
                    await page.wait_for_load_state("networkidle")
                    modal = await page.query_selector(".employment-company-group-modal")
                    modal_company_name = await modal.query_selector(".employment-group-title__content").inner_text()
                    recruitment_title_elem = await item.query_selector(".employment-group-item__title-content.ng-binding")
                    recruitment_title = await recruitment_title_elem.inner_text() if recruitment_title_elem else "N/A"
                    end_time_elem = await item.query_selector(".employment-group-item__end-time")
                    end_time = await end_time_elem.inner_text() if end_time_elem else None
                    anchor = await item.query_selector("a.employment-company-anchor")
                    link = ""
                    if anchor:
                        href_modal = await anchor.get_attribute("href")
                        link = f"https://jasoseol.com{href_modal}" if href_modal.startswith("/") else href_modal
                    companies.append({
                        "start_date": await calendar_item.get_attribute("day"),
                        "end_date": end_time,
                        "employment_id": await item.get_attribute("employment_id"),
                        "link": link,
                        "company_name": modal_company_name,
                        "recruitment_title": recruitment_title,
                        "jobs": []
                    })
                    logger.info("모달 방식: 탐지된 기업(모달) - %s", modal_company_name)
                    close_button = await page.query_selector("button.modal-close-btn")
                    if close_button:
                        await close_button.click()
                        await page.wait_for_selector(".employment-company-group-modal", state="hidden", timeout=5000)
                    else:
                        logger.warning("모달 close button not found, skipping close action")
            return companies
        else:
            logger.info("모달 방식: employment-group-item 요소가 없으므로, 단일 정보를 추출합니다.")
            link_elem = await calendar_item.query_selector("a.company")
            href = await link_elem.get_attribute("href") if link_elem else ""
            start_date = await calendar_item.get_attribute("day")
            employment_id = await calendar_item.get_attribute("employment_id")
            company_elem = await calendar_item.query_selector("div.company-name span")
            company_name = await company_elem.inner_text() if company_elem else "N/A"
            recruitment_title = f"{company_name} 채용 공고"
            single_company = {
                "start_date": start_date,
                "end_date": None,
                "employment_id": employment_id,
                "link": "https://jasoseol.com" + href if href and href.startswith("/") else href,
                "company_name": company_name,
                "recruitment_title": recruitment_title,
                "jobs": []
            }
            logger.info("모달 방식: 단일 기업 추출 - %s", company_name)
            return [single_company]
    except Exception as e:
        logger.error("모달 추출 중 오류: %s", e)
        await page.screenshot(path="error_screenshot_modal_fail.png")
        return []

async def integrated_crawler(target_date, filter_company=None):
    async with async_playwright() as p:
        await ensure_logged_in(p)
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-extensions", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            storage_state="state.json",
            viewport={"width": 800, "height": 600}
        )
        page = await context.new_page()
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())
        await page.goto("https://jasoseol.com/recruit")
        try:
            await page.click("div.popup-close, div[data-sentry-component='PopupAdvertise'] button", timeout=5000)
            logger.info("메인 페이지 팝업 닫기 완료")
        except Exception as e:
            logger.info("메인 페이지 팝업 없음 또는 닫기 실패: %s", e)
        logger.info("선택한 날짜: %s", target_date)
        calendar_items = await page.query_selector_all(f"div.calendar-item[day='{target_date}']")
        max_attempts = 12
        attempts = 0
        while not calendar_items and attempts < max_attempts:
            logger.info("캘린더에 %s가 없습니다. 다음 달로 이동합니다. (시도 %s)", target_date, attempts + 1)

            # 1. 다음 달 버튼 선택자 수정
            next_button_selector = "div.calendar-nav img[ng-click='addMonth(1)']"
            current_month_display_selector = "div.calendar-nav > span.current"

            # (선택 사항) 클릭 전 현재 월 확인
            current_month_element = await page.query_selector(current_month_display_selector)
            current_month_text = await current_month_element.inner_text() if current_month_element else ""

            next_button = await page.query_selector(next_button_selector)
            if not next_button:
                logger.info("다음 달 버튼을 찾을 수 없습니다.")
                break

            await next_button.click()
            logger.info("다음 달 버튼 클릭 완료.")

            # 2. 대기 로직 개선 (월 표시 변경 대기 예시)
            try:
                await page.wait_for_function(
                    f"""(selector, previous_text) => {{
                        const element = document.querySelector(selector);
                        // 현재 텍스트가 존재하고 이전 텍스트와 다른지 확인
                        return element && element.innerText && element.innerText !== previous_text;
                    }}""",
                    (current_month_display_selector, current_month_text),
                    timeout=10000 # 최대 10초 대기
                )
                new_month_element = await page.query_selector(current_month_display_selector)
                new_month_text = await new_month_element.inner_text() if new_month_element else "N/A"
                logger.info(f"다음 달 로드 확인 (표시: {new_month_text}).")
                # 필요시 추가 대기
                await page.wait_for_timeout(500) # 예: 0.5초 추가 대기

            except Exception as wait_e:
                logger.warning(f"다음 달 로드 확인 중 타임아웃 또는 오류 발생: {wait_e}")
                # 실패 시 디버깅 정보 저장
                await page.screenshot(path=f"debug_wait_fail_{target_date}.png")
                break # 루프 중단

            # 날짜 항목 다시 검색
            calendar_items = await page.query_selector_all(f"div.calendar-item[day='{target_date}']")
            attempts += 1

        if not calendar_items:
            logger.info("%s에 해당하는 캘린더 아이템을 찾을 수 없습니다.", target_date)
            await browser.close()
            return

        for idx, item in enumerate(calendar_items):
            companies_from_item = []
            company_links = await item.query_selector_all("a.company")
            for comp in company_links:
                label_elem = await comp.query_selector("div.calendar-label.start")
                if label_elem:
                    label_text = (await label_elem.inner_text()).strip()
                    if label_text == "시":
                        href = await comp.get_attribute("href")
                        company_elem = await comp.query_selector("div.company-name span")
                        company_name = await company_elem.inner_text() if company_elem else "N/A"
                        start_date = await item.get_attribute("day")
                        employment_id = await item.get_attribute("employment_id")
                        recruitment_title = f"{company_name} 채용 공고"
                        companies_from_item.append({
                            "start_date": start_date,
                            "end_date": None,
                            "employment_id": employment_id,
                            "link": "https://jasoseol.com" + href if href and href.startswith("/") else href,
                            "company_name": company_name,
                            "recruitment_title": recruitment_title,
                            "jobs": []
                        })
            if not companies_from_item:
                logger.info("캘린더 아이템 #%s: a.company 방식으로 기업을 찾지 못함. 모달 방식으로 처리", idx+1)
                companies_from_item = await extract_modal_data(page, item)
                logger.info("캘린더 아이템 #%s: 모달 방식으로 탐지된 기업 수 = %s", idx+1, len(companies_from_item))
            if filter_company:
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
                if not companies_from_item:
                    logger.info("캘린더 아이템 #%s에서 주어진 기업 목록에 해당하는 기업을 찾지 못함", idx+1)
                    continue
            for company in companies_from_item:
                logger.info("디테일 크롤링 시작: %s - %s", company['company_name'], company['link'])
                try:
                    detail_page = await context.new_page()
                    try:
                        await detail_page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())
                        await detail_page.goto(company["link"])
                        try:
                            await detail_page.click("div.popup-close, div[data-sentry-component='PopupAdvertise'] button", timeout=5000)
                            logger.info("디테일 페이지 팝업 닫기 완료")
                        except Exception as e:
                            logger.info("디테일 페이지 팝업 없음 또는 닫기 실패: %s", e)
                        try:
                            await detail_page.evaluate("""() => {
                                const popup = document.querySelector("div[data-sentry-component='PopupAdvertise']");
                                if (popup) { popup.remove(); }
                            }""")
                            logger.info("디테일 페이지 광고 배너 강제 제거 완료")
                        except Exception as e:
                            logger.info("광고 배너 강제 제거 실패: %s", e)
                    except Exception as e:
                        logger.info("디테일 페이지 접속 오류: %s - %s", company['link'], e)
                        await detail_page.close()
                        continue

                    try:
                        selector_end_date = r"div.flex.gap-\[4px\].mb-\[20px\].body5"
                        await detail_page.wait_for_selector(selector_end_date, timeout=15000)
                        date_div = await detail_page.query_selector(selector_end_date)
                        spans = await date_div.query_selector_all("span")
                        end_date = (await spans[2].inner_text()).strip() if len(spans) >= 4 else None
                    except Exception as e:
                        logger.info("종료일 크롤링 오류: %s - %s", company['link'], e)
                        end_date = None
                    company["end_date"] = end_date

                    try:
                        link_elem = await detail_page.query_selector("a.flex-grow:has(button:has-text('채용 사이트'))")
                        recruitment_link = await link_elem.get_attribute("href") if link_elem else None
                    except Exception as e:
                        logger.info("채용 사이트 링크 크롤링 오류: %s - %s", company['link'], e)
                        recruitment_link = None
                    company["recruitment_link"] = recruitment_link

                    try:
                        await detail_page.wait_for_selector("ul.shadow2", timeout=5000)
                        container = await detail_page.query_selector("ul.shadow2")
                        job_elements = await container.query_selector_all("li.flex.justify-center")
                    except Exception as e:
                        logger.info("ul.shadow2 not found, fallback to li.flex.justify-center: %s", e)
                        job_elements = await detail_page.query_selector_all("li.flex.justify-center")

                    jobs = []
                    for idx, li_elem in enumerate(job_elements):
                        recruitment_type = recruitment_title = None
                        try:
                            spans = await li_elem.query_selector_all("span")
                            if len(spans) >= 2:
                                recruitment_type = (await spans[0].inner_text()).strip()
                                recruitment_title = (await spans[1].inner_text()).strip()
                        except Exception as e:
                            logger.info("Error extracting job type/title for job #%s: %s", idx+1, e)

                        essay_questions = []
                        try:
                            button = await li_elem.query_selector("button:has-text('자기소개서 쓰기')")
                            if button:
                                await button.click()
                                essay_blocks = await li_elem.query_selector_all("div.font-normal.mb-\\[8px\\]")
                                visible_blocks = [block for block in essay_blocks if await block.is_visible()]
                                if visible_blocks:
                                    for block in visible_blocks:
                                        q_elem = await block.query_selector("div.text-\\[14px\\]")
                                        l_elem = await block.query_selector("div.text-\\[10px\\]")
                                        if q_elem and l_elem:
                                            q_text = (await q_elem.inner_text()).strip()
                                            l_text = (await l_elem.inner_text()).strip()
                                            essay_questions.append({
                                                "question": q_text,
                                                "limit": l_text
                                            })
                                else:
                                    logger.info("No visible essay section found for job #%s", idx+1)
                            else:
                                logger.info("Job #%s: '자기소개서 쓰기' button not found.", idx+1)
                        except Exception as e:
                            logger.info("Error extracting essay questions for job #%s: %s", idx+1, e)

                        jobs.append({
                            "recruitment_type": recruitment_type,
                            "recruitment_title": recruitment_title,
                            "essay_questions": essay_questions
                        })
                    company["jobs"] = jobs
                    logger.info("디테일 크롤링 완료: %s", company['company_name'])
                    await detail_page.close()
                    yield company
                except Exception as e:
                    logger.info("디테일 페이지 처리 중 예외 발생: %s", e)
                    continue

        await browser.close()
        
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
    print(json.dumps(companies_data))
