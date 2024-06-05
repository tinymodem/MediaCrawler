import asyncio
from playwright.async_api import async_playwright
from tools import utils
import os
from pathlib import Path

async def login_by_cookies(browser_context, cookie_str):
    for key, value in utils.convert_str_cookie_to_dict(cookie_str).items():
        await browser_context.add_cookies([{
            'name': key,
            'value': value,
            'domain': ".zhihu.com",
            'path': "/"
        }])

async def launch_browser(chromium, playwright_proxy, user_agent, headless=True, save_login_state=True):
    """Launch browser and create browser context"""
    if save_login_state:
        print("Save login state to avoid login every time")
        # feat issue #14
        # we will save login state to avoid login every time
        user_data_dir = os.path.join(os.getcwd(), "zhihu_browser_data")  # type: ignore
        browser_context = await chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            accept_downloads=True,
            headless=headless,
            proxy=playwright_proxy,  # type: ignore
            viewport={"width": 700, "height": 932},
            device_scale_factor=4,
            user_agent=user_agent
        )
        return browser_context
    else:
        browser = await chromium.launch(headless=headless, proxy=playwright_proxy)  # type: ignore
        browser_context = await browser.new_context(
            viewport={"width": 700, "height": 932},
            device_scale_factor=4,
            user_agent=user_agent
        )
        return browser_context



async def main():
    async with async_playwright() as p:
        browser_context = await launch_browser(p.chromium, None, utils.get_user_agent(), headless=True, save_login_state=True)
        with open("cookies.txt", "r") as f:
            cookie_str = f.read()
        await login_by_cookies(browser_context, cookie_str)
        page = await browser_context.new_page()
        await page.goto("https://www.zhihu.com/question/426489276/answer/1675707394")
        
        # 获取页面高度
        page_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = await page.evaluate("window.innerHeight")
        print(f"page_height: {page_height}, viewport_height: {viewport_height}")

        # 定义每次滚动的步长（稍小于视口高度以保留重叠）
        scroll_step = viewport_height - 200  # 保留100像素的重叠部分

        # 初始化截图索引
        screenshot_index = 1
        Path("screenshot").mkdir(exist_ok=True)
        for offset in range(0, page_height, scroll_step):
            # 截取截图
            await page.screenshot(path=Path("screenshot") / f"screenshot_{screenshot_index}.png", full_page=False)
            screenshot_index += 1

            # 滚动页面，但确保不超过页面底部
            next_offset = min(offset + scroll_step, page_height - viewport_height)
            await page.evaluate(f"window.scrollTo(0, {next_offset})")

        # # Optionally, take a screenshot
        # await page.screenshot(path="1675707394.png", full_page=True)
        
        # # Optionally, extract content
        content = await page.content()
        with open("content.html", "w") as f:
            f.write(content)
        # print(content)
        
        await browser_context.close()

asyncio.run(main())
