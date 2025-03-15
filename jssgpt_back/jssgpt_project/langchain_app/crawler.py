import sys
import asyncio
import json
import logging
import os
from playwright.async_api import async_playwright

# 모든 로그를 stderr로 출력 (stdout에는 오직 최종 JSON만 출력)
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def ensure_logged_in(playwright):
    """
    state.json 파일이 없으면 로그인 과정을 수행하여 state.json에 세션 상태를 저장합니다.
    """
    if os.path.exists("state.json"):
        logger.debug("이미 로그인 상태가 저장되어 있습니다.")
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
        logger.debug("팝업 닫기 완료")
    except Exception as e:
        logger.debug("팝업이 없거나 닫기 실패: %s", e)

    try:
        await page.evaluate("document.querySelector('div[data-sentry-component=\"PopupAdvertise\"]').remove()")
        logger.debug("팝업 요소 제거 완료")
    except Exception as e:
        logger.debug("팝업 요소 제거 불필요: %s", e)

    try:
        await page.click("button:has-text('회원가입/로그인')", timeout=10000)
        logger.debug("로그인 버튼 클릭 완료")
    except Exception as e:
        logger.debug("로그인 버튼 클릭 실패: %s", e)
        await browser.close()
        return

    try:
        await page.wait_for_selector("input[name='id']", timeout=15000)
        logger.debug("로그인 모달 로드 완료")
    except Exception as e:
        logger.debug("로그인 모달 로드 실패: %s", e)
        await browser.close()
        return

    await page.fill("input[name='id']", "geuloing@gmail.com")
    await page.fill("input[name='password']", "jssgpt564!")
    
    try:
        login_button = page.get_by_text("로그인", exact=True)
        await login_button.click(timeout=10000)
        logger.debug("로그인 버튼 클릭 완료")
    except Exception as e:
        logger.debug("로그인 버튼 클릭 실패: %s", e)
        await page.screenshot(path="error_screenshot_click_fail.png")
        await browser.close()
        return

    try:
        await page.wait_for_selector("div[data-sentry-component='PopupAdvertise']", timeout=15000)
        logger.debug("로그인 성공 후 팝업 감지!")
        await page.click("div[data-sentry-component='PopupAdvertise'] button", timeout=5000)
        logger.debug("로그인 성공 후 팝업 닫기 완료")
    except Exception as e:
        logger.debug("팝업 감지 실패. 텍스트 또는 URL로 로그인 확인 진행: %s", e)
        try:
            await page.wait_for_selector("span.text-gray-900:has-text('의 맞춤공고예요.')", timeout=15000)
            logger.debug("로그인 성공! 텍스트 확인 완료")
        except Exception as e:
            logger.debug("로그인 성공 텍스트 확인 실패: %s", e)
            current_url = page.url
            if "dashboard" in current_url:
                logger.debug("로그인 성공 (URL 확인)!")
            else:
                await page.screenshot(path="error_screenshot_login_fail.png")
                logger.debug("로그인 실패! 스크린샷 저장.")
                await browser.close()
                return

    await context.storage_state(path="state.json")
    logger.debug("로그인 세션 저장 완료.")
    await browser.close()

async def extract_modal_data(page, calendar_item):
    """
    선택한 날짜의 calendar_item 내에 있는 모든 기업 정보를 추출합니다.
    만약 각 기업 요소(.employment-group-item)가 개별적으로 a.company 링크를 가지고 있다면 이를 이용해
    정보를 추출하고, 그렇지 않으면 기존 모달 방식(jss2.html)을 통해 여러 기업 정보를 가져옵니다.
    """
    companies = []
    try:
        # calendar_item 내부의 모든 기업 요소를 선택합니다.
        employment_items = await calendar_item.query_selector_all(".employment-group-item")
        if employment_items:
            for item in employment_items:
                # 시각 표시 요소가 있는지 확인 (예: <div class="calendar-label start">시</div>)
                label_elem = await calendar_item.query_selector("div.calendar-label.start")
                if label_elem:
                    label_text = (await label_elem.inner_text()).strip()
                    if label_text != "시":
                        continue  # '시'인 기업만 처리
                # 각 employment item 내부에서 a.company 요소를 찾습니다.
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
                else:
                    # a.company 요소가 없으면, 기존 모달 방식으로 해당 item의 정보를 추출합니다.
                    logger.info("a.company 링크가 없으므로 모달 방식으로 해당 기업 정보를 추출합니다.")
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
                    # 모달 닫기
                    close_button = await page.query_selector("button.modal-close-btn")
                    if close_button:
                        await close_button.click()
                        await page.wait_for_selector(".employment-company-group-modal", state="hidden", timeout=5000)
                    else:
                        logger.warning("Modal close button not found, skipping close action")
            return companies
        else:
            # 만약 employment_items가 없다면 fallback: 기존 방식으로 단일 정보를 추출
            logger.info("employment-group-item 요소가 없으므로, 단일 정보를 추출합니다.")
            link_elem = await calendar_item.query_selector("a.company")
            href = await link_elem.get_attribute("href") if link_elem else ""
            start_date = await calendar_item.get_attribute("day")
            employment_id = await calendar_item.get_attribute("employment_id")
            company_elem = await calendar_item.query_selector("div.company-name span")
            company_name = await company_elem.inner_text() if company_elem else "N/A"
            recruitment_title = f"{company_name} 채용 공고"
            return [{
                "start_date": start_date,
                "end_date": None,
                "employment_id": employment_id,
                "link": "https://jasoseol.com" + href if href and href.startswith("/") else href,
                "company_name": company_name,
                "recruitment_title": recruitment_title,
                "jobs": []
            }]
    except Exception as e:
        logger.error(f"Error in modal extraction: {str(e)}")
        await page.screenshot(path="error_screenshot_modal_fail.png")
        return []

async def integrated_crawler(target_date):
    """
    target_date: 크롤링할 날짜 (YYYYMMDD 문자열)
    로그인 상태가 저장된 state.json 파일을 이용해 크롤링을 진행합니다.
    """
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

        # 불필요한 리소스 차단
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())

        await page.goto("https://jasoseol.com/recruit")
        try:
            await page.click("div.popup-close, div[data-sentry-component='PopupAdvertise'] button", timeout=5000)
            logger.debug("팝업 닫기 완료")
        except Exception as e:
            logger.debug("팝업 없음 또는 닫기 실패: %s", e)

        logger.debug("선택한 날짜: %s", target_date)
        calendar_items = await page.query_selector_all(f"div.calendar-item[day='{target_date}']")
        max_attempts = 12
        attempts = 0
        while not calendar_items and attempts < max_attempts:
            logger.debug("캘린더에 %s가 없습니다. 다음 달로 이동합니다. (시도 %s)", target_date, attempts + 1)
            next_button = await page.query_selector('[ng-click="addMonth(1)"]')
            if not next_button:
                logger.debug("다음 달 버튼을 찾을 수 없습니다.")
                break
            await next_button.click()
            await page.wait_for_timeout(1000)
            calendar_items = await page.query_selector_all(f"div.calendar-item[day='{target_date}']")
            attempts += 1

        if not calendar_items:
            logger.debug("%s에 해당하는 캘린더 아이템을 찾을 수 없습니다.", target_date)
            await browser.close()
            return

        for item in calendar_items:
            label_elem = await item.query_selector("div.calendar-label.start")
            if label_elem:
                label_text = (await label_elem.inner_text()).strip()
                if label_text == "시":
                    modal_data = await extract_modal_data(page, item)
                    for company in modal_data:
                        logger.debug("디테일 크롤링 시작: %s - %s", company['company_name'], company['link'])
                        try:
                            await page.goto(company["link"])
                            try:
                                await page.click("div.popup-close, div[data-sentry-component='PopupAdvertise'] button", timeout=5000)
                                logger.debug("디테일 페이지 팝업 닫기 완료")
                            except Exception as e:
                                logger.debug("디테일 페이지 팝업 없음 또는 닫기 실패: %s", e)
                            try:
                                await page.evaluate("""() => {
                                    const popup = document.querySelector("div[data-sentry-component='PopupAdvertise']");
                                    if (popup) { popup.remove(); }
                                }""")
                                logger.debug("디테일 페이지 광고 배너 강제 제거 완료")
                            except Exception as e:
                                logger.debug("광고 배너 강제 제거 실패: %s", e)
                        except Exception as e:
                            logger.debug("디테일 페이지 접속 오류: %s - %s", company['link'], e)
                            continue

                        try:
                            selector_end_date = r"div.flex.gap-\[4px\].mb-\[20px\].body5"
                            await page.wait_for_selector(selector_end_date, timeout=15000)
                            date_div = await page.query_selector(selector_end_date)
                            spans = await date_div.query_selector_all("span")
                            end_date = (await spans[2].inner_text()).strip() if len(spans) >= 4 else None
                        except Exception as e:
                            logger.debug("종료일 크롤링 오류: %s - %s", company['link'], e)
                            end_date = None
                        company["end_date"] = end_date

                        try:
                            link_elem = await page.query_selector("a.flex-grow:has(button:has-text('채용 사이트'))")
                            recruitment_link = await link_elem.get_attribute("href") if link_elem else None
                        except Exception as e:
                            logger.debug("채용 사이트 링크 크롤링 오류: %s - %s", company['link'], e)
                            recruitment_link = None
                        company["recruitment_link"] = recruitment_link

                        try:
                            await page.wait_for_selector("ul.shadow2", timeout=5000)
                            container = await page.query_selector("ul.shadow2")
                            job_elements = await container.query_selector_all("li.flex.justify-center")
                        except Exception as e:
                            logger.debug("ul.shadow2 not found, fallback to li.flex.justify-center: %s", e)
                            job_elements = await page.query_selector_all("li.flex.justify-center")

                        jobs = []
                        for idx, li_elem in enumerate(job_elements):
                            recruitment_type = recruitment_title = None
                            try:
                                spans = await li_elem.query_selector_all("span")
                                if len(spans) >= 2:
                                    recruitment_type = (await spans[0].inner_text()).strip()
                                    recruitment_title = (await spans[1].inner_text()).strip()
                            except Exception as e:
                                logger.debug("Error extracting job type/title for job #%s: %s", idx+1, e)

                            essay_questions = []
                            try:
                                button = await li_elem.query_selector("button:has-text('자기소개서 쓰기')")
                                if button:
                                    await button.click()
                                    essay_blocks = await li_elem.query_selector_all("div.font-normal.mb-\\[8px\\]")
                                    visible_blocks = []
                                    for block in essay_blocks:
                                        if await block.is_visible():
                                            visible_blocks.append(block)
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
                                        logger.debug("No visible essay section found for job #%s", idx+1)
                                else:
                                    logger.debug("Job #%s: '자기소개서 쓰기' button not found.", idx+1)
                            except Exception as e:
                                logger.debug("Error extracting essay questions for job #%s: %s", idx+1, e)

                            jobs.append({
                                "recruitment_type": recruitment_type,
                                "recruitment_title": recruitment_title,
                                "essay_questions": essay_questions
                            })
                        company["jobs"] = jobs
                        logger.debug("디테일 크롤링 완료: %s", company['company_name'])
                        yield company  # 각 회사를 즉시 반환

        await browser.close()

if __name__ == "__main__":
    target_date = input("크롤링할 날짜 (YYYYMMDD)를 입력하세요: ")
    companies_data = []
    async def collect_data():
        async for company in integrated_crawler(target_date):
            companies_data.append(company)
    asyncio.run(collect_data())
    print(json.dumps(companies_data))
