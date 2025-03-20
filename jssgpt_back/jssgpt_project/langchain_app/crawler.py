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
        logger.info("팝업 감지 실패: %s", e)
        try:
            await page.wait_for_selector("span.text-gray-900:has-text('의 맞춤공고예요.')", timeout=15000)
            logger.info("로그인 성공! 텍스트 확인 완료")
        except Exception as e:
            logger.info("로그인 성공 텍스트 확인 실패: %s", e)
            if "dashboard" in page.url:
                logger.info("로그인 성공 (URL 확인)!")
            else:
                await page.screenshot(path="error_screenshot_login_fail.png")
                logger.info("로그인 실패! 스크린샷 저장.")
                await browser.close()
                return
    await context.storage_state(path="state.json")
    logger.info("로그인 세션 저장 완료.")
    await browser.close()

async def get_start_date_from_detail(page, company_url):
    """
    상세 페이지에서 첫 번째 span.text-gray-700의 텍스트를 파싱하여 시작 날짜를 반환합니다.
    """
    try:
        await page.goto(company_url)
        await page.wait_for_selector("span.text-gray-700", timeout=10000)
        span_elem = await page.query_selector("span.text-gray-700")
        text = await span_elem.inner_text()
        from datetime import datetime
        start_date = datetime.strptime(text.strip(), "%Y년 %m월 %d일 %H:%M").date()
        logger.info("상세 페이지에서 시작 날짜 파싱 완료: %s", start_date)
        return start_date
    except Exception as e:
        logger.error("상세 페이지 시작 날짜 파싱 실패: %s", e)
        return None

async def extract_modal_data(page, calendar_item, mode="start", target_date=None):
    companies = []
    try:
        employment_items = await calendar_item.query_selector_all(".employment-group-item")
        if employment_items:
            for item in employment_items:
                label_elem = await item.query_selector("div.calendar-label.start")
                if label_elem:
                    label_text = (await label_elem.inner_text()).strip()
                    if mode == "start" and label_text != "시":
                        continue
                    if mode == "end" and label_text != "끝":
                        continue
                link_elem = await item.query_selector("a.company")
                if link_elem:
                    href = await link_elem.get_attribute("href")
                    company_elem = await item.query_selector("div.company-name span")
                    company_name = await company_elem.inner_text() if company_elem else "N/A"
                    if mode == "start":
                        start_date = await calendar_item.get_attribute("day")
                        end_date = None
                    else:
                        start_date = None
                        end_date = target_date
                    employment_id = await item.get_attribute("employment_id")
                    recruitment_title_elem = await item.query_selector(".employment-group-item__title-content.ng-binding")
                    recruitment_title = await recruitment_title_elem.inner_text() if recruitment_title_elem else f"{company_name} 채용 공고"
                    company_data = {
                        "start_date": start_date,
                        "end_date": end_date,
                        "employment_id": employment_id,
                        "link": "https://jasoseol.com" + href if href and href.startswith("/") else href,
                        "company_name": company_name,
                        "recruitment_title": recruitment_title,
                        "jobs": []
                    }
                    if mode == "end":
                        start_date_detail = await get_start_date_from_detail(page, company_data["link"])
                        if start_date_detail:
                            company_data["start_date"] = start_date_detail.strftime("%Y%m%d")
                    companies.append(company_data)
                    logger.info("모달 방식: 탐지된 기업 - %s", company_name)
                else:
                    logger.info("모달 방식: a.company 링크 없음. 추가 처리 필요.")
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
            if mode == "start":
                start_date_val = start_date
                end_date_val = None
            else:
                start_date_val = None
                end_date_val = target_date
            company_data = {
                "start_date": start_date_val,
                "end_date": end_date_val,
                "employment_id": employment_id,
                "link": "https://jasoseol.com" + href if href and href.startswith("/") else href,
                "company_name": company_name,
                "recruitment_title": recruitment_title,
                "jobs": []
            }
            if mode == "end":
                start_date_detail = await get_start_date_from_detail(page, company_data["link"])
                if start_date_detail:
                    company_data["start_date"] = start_date_detail.strftime("%Y%m%d")
            logger.info("모달 방식: 단일 기업 추출 - %s", company_name)
            return [company_data]
    except Exception as e:
        logger.error("모달 추출 중 오류: %s", e)
        await page.screenshot(path="error_screenshot_modal_fail.png")
        return []

async def integrated_crawler(target_date, filter_company=None, mode="start"):
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
        logger.info("선택한 날짜: %s, 모드: %s", target_date, mode)
        if mode == "start":
            calendar_items = await page.query_selector_all(f"div.calendar-item[day='{target_date}']")
        else:
            calendar_items = await page.query_selector_all("div.calendar-item")
        max_attempts = 12
        attempts = 0
        while mode == "end" and not calendar_items and attempts < max_attempts:
            logger.info("캘린더 항목이 없습니다. 다음 달로 이동합니다. (시도 %s)", attempts + 1)
            next_button = await page.query_selector('[ng-click="addMonth(1)"]')
            if not next_button:
                logger.info("다음 달 버튼을 찾을 수 없습니다.")
                break
            await next_button.click()
            await page.wait_for_timeout(1000)
            calendar_items = await page.query_selector_all("div.calendar-item")
            attempts += 1

        if not calendar_items:
            logger.info("캘린더 항목을 찾을 수 없습니다.")
            await browser.close()
            return

        for idx, item in enumerate(calendar_items):
            companies_from_item = []
            company_links = await item.query_selector_all("a.company")
            for comp in company_links:
                label_elem = await comp.query_selector("div.calendar-label.start")
                if label_elem:
                    label_text = (await label_elem.inner_text()).strip()
                    if mode == "start" and label_text != "시":
                        continue
                    if mode == "end" and label_text != "끝":
                        continue
                href = await comp.get_attribute("href")
                company_elem = await comp.query_selector("div.company-name span")
                company_name = await company_elem.inner_text() if company_elem else "N/A"
                if mode == "start":
                    start_date = await item.get_attribute("day")
                    end_date = None
                else:
                    start_date = None
                    end_date = target_date
                employment_id = await item.get_attribute("employment_id")
                recruitment_title_elem = await comp.query_selector(".employment-group-item__title-content.ng-binding")
                recruitment_title = await recruitment_title_elem.inner_text() if recruitment_title_elem else f"{company_name} 채용 공고"
                company_data = {
                    "start_date": start_date,
                    "end_date": end_date,
                    "employment_id": employment_id,
                    "link": "https://jasoseol.com" + href if href and href.startswith("/") else href,
                    "company_name": company_name,
                    "recruitment_title": recruitment_title,
                    "jobs": []
                }
                if mode == "end":
                    start_date_detail = await get_start_date_from_detail(page, company_data["link"])
                    if start_date_detail:
                        company_data["start_date"] = start_date_detail.strftime("%Y%m%d")
                companies_from_item.append(company_data)
                logger.info("캘린더 아이템 #%s: 탐지된 기업 - %s", idx + 1, company_name)
            if not companies_from_item:
                logger.info("캘린더 아이템 #%s: 기업을 찾지 못함. 모달 방식으로 처리.", idx + 1)
                companies_from_item = await extract_modal_data(page, item, mode, target_date)
                logger.info("캘린더 아이템 #%s: 모달 방식으로 탐지된 기업 수 = %s", idx + 1, len(companies_from_item))
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
                    logger.info("캘린더 아이템 #%s에서 주어진 기업을 찾지 못함", idx + 1)
                    continue
            for company in companies_from_item:
                logger.info("디테일 크롤링 시작: %s - %s", company['company_name'], company['link'])
                try:
                    detail_page = await context.new_page()
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
                        logger.info("디테일 페이지 광고 배너 제거 완료")
                    except Exception as e:
                        logger.info("광고 배너 제거 실패: %s", e)
                    try:
                        selector_end_date = r"div.flex.gap-\[4px\].mb-\[20px\].body5"
                        await detail_page.wait_for_selector(selector_end_date, timeout=15000)
                        date_div = await detail_page.query_selector(selector_end_date)
                        spans = await date_div.query_selector_all("span")
                        end_date_text = (await spans[2].inner_text()).strip() if len(spans) >= 4 else None
                    except Exception as e:
                        logger.info("종료일 크롤링 오류: %s - %s", company['link'], e)
                        end_date_text = None
                    company["end_date"] = end_date_text
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
                    for idx_job, li_elem in enumerate(job_elements):
                        recruitment_type = recruitment_title = None
                        try:
                            spans = await li_elem.query_selector_all("span")
                            if len(spans) >= 2:
                                recruitment_type = (await spans[0].inner_text()).strip()
                                recruitment_title = (await spans[1].inner_text()).strip()
                        except Exception as e:
                            logger.info("Error extracting job type/title for job #%s: %s", idx_job + 1, e)
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
                                    logger.info("No visible essay section found for job #%s", idx_job + 1)
                            else:
                                logger.info("Job #%s: '자기소개서 쓰기' button not found.", idx_job + 1)
                        except Exception as e:
                            logger.info("Error extracting essay questions for job #%s: %s", idx_job + 1, e)
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

async def main(target_date, filter_company=None, mode="start"):
    async for company in integrated_crawler(target_date, filter_company, mode):
        yield company

if __name__ == "__main__":
    target_date = input("크롤링할 날짜 (YYYYMMDD)를 입력하세요: ").strip()
    mode = input("크롤링 기준을 입력하세요 (start/end): ").strip().lower() or "start"
    company_name = input("기업명 (선택, 여러 개는 쉼표로 구분, 없으면 엔터): ").strip() or None
    if company_name:
        company_names = [name.strip() for name in company_name.split(",") if name.strip()]
    else:
        company_names = None
    companies_data = []
    async def collect_data():
        async for company in main(target_date, company_names, mode):
            companies_data.append(company)
    asyncio.run(collect_data())
    print(json.dumps(companies_data, ensure_ascii=False, indent=2))
