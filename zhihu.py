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
            # 3:4
            viewport={"width": 700, "height": 1033},
            device_scale_factor=4,
            user_agent=user_agent
        )
        return browser_context
    else:
        browser = await chromium.launch(headless=headless, proxy=playwright_proxy)  # type: ignore
        browser_context = await browser.new_context(
            viewport={"width": 700, "height": 1033},
            device_scale_factor=4,
            user_agent=user_agent
        )
        return browser_context
    

async def url_to_screenshots(url):
    async with async_playwright() as p:
        browser_context = await launch_browser(p.chromium, None, utils.get_user_agent(), headless=True, save_login_state=True)
        with open("cookies.txt", "r") as f:
            cookie_str = f.read()
        await login_by_cookies(browser_context, cookie_str)
        page = await browser_context.new_page()
        await page.goto(url)

        # 使用 JavaScript 修改 --app-font-size 变量
        await page.evaluate(f'''() => {{
            document.documentElement.style.setProperty('--app-font-size', '30px');
        }}''')

        # 检查修改结果
        font_size = await page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--app-font-size")')
        print(f"Modified --app-font-size: {font_size}")

        
        # 获取页面高度
        page_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = await page.evaluate("window.innerHeight")
        print(f"page_height: {page_height}, viewport_height: {viewport_height}")

        # 定义每次滚动的步长（稍小于视口高度以保留重叠）
        scroll_step = viewport_height - 250  # 保留100像素的重叠部分

        # 初始化截图索引
        screenshot_index = 1
        output_dir = Path("output") / url.split("/")[-1]
        print(f"Output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        # 定义截图区域
        clip_area = {
            'x': 20,  # 区域的起始点 x 坐标
            'y': 50,  # 区域的起始点 y 坐标
            'width': 670,  # 区域的宽度
            'height': 933  # 区域的高度
        }
        # 控制截图到第一个回答结束。
        for offset in range(0, page_height, scroll_step):
            # to follow dictionary order.
            screenshot_path = output_dir / f"{screenshot_index:02}.png"
            # 截取截图
            await page.screenshot(path=screenshot_path, clip=clip_area)
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


async def batch_url_to_screenshots(urls):
    for url in urls:
        print(f"Start crawling {url}")
        await url_to_screenshots(url)


if __name__ == '__main__':
    # asyncio.run(url_to_screenshots("https://www.zhihu.com/question/426489276/answer/1675707394"))
    with open("urls.txt", "r") as f:
        urls = f.read().split("\n")
    asyncio.run(batch_url_to_screenshots(urls))
