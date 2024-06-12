import asyncio
from playwright.async_api import async_playwright
from tools import utils
import os
from pathlib import Path
import argparse

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
            viewport={"width": 1200, "height": 1033},
            device_scale_factor=4,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
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
    

async def url_to_screenshots(url, url_file_name=""):
    async with async_playwright() as p:
        browser_context = await launch_browser(p.chromium, None,
                                               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", headless=True, save_login_state=True)
        with open("cookies.txt", "r") as f:
            cookie_str = f.read()
        await login_by_cookies(browser_context, cookie_str)
        page = await browser_context.new_page()
        # 添加一些常见的请求头信息
        await page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.zhihu.com/',
            "X-Requested-With": "fetch"
        })

        # 监听特定的请求并记录响应
        async def request_listener(request):
            if "https://www.zhihu.com/api/v4/comment_v5/answers/2825317069/root_comment?order_by=score&limit=20&offset=" in request.url:
                print(f"Intercepted request URL: {request.url}")
                response = await request.response()
                if response:
                    print(f"Response status: {response.status}")
                    if response.status == 403:
                        # 抓取响应体以了解更多信息
                        body = await response.text()
                        print(f"Response body: {body}")

        page.on('request', request_listener)

        print(f"Navigating to {url}...")
        await page.goto(url)

        # 等待页面加载完成
        await page.wait_for_load_state('networkidle')
        print("Page loaded.")

        # 使用更精确的 CSS 选择器定位所有包含“条评论”的按钮
        await page.wait_for_selector('button:has-text("条评论")')
        comment_buttons = page.locator('button:has-text("条评论")')
        
        # 获取按钮数量以便调试
        count = await comment_buttons.count()
        print(f"Found {count} comment buttons.")

        if count < 2:
            print("Less than 2 comment buttons found. Exiting.")
            return

        # 模拟鼠标移动到按钮并点击
        print("Hovering over the second comment button...")
        button = comment_buttons.nth(1)
        await button.hover()
        await page.wait_for_timeout(10000)  # 等待0.5秒
        await page.screenshot(path="debug_hover.png")

        print("Clicking the second comment button...")
        await button.click()
        print("Second comment button clicked.")
    
        # 等待一段时间以确保内容加载
        await page.wait_for_timeout(60000)  # 等待5秒

        # 截取点击后的页面截图
        await page.screenshot(path="after_click.png")
        print("Screenshot taken after click.")

        # await page.wait_for_selector('.CommentContent', timeout=10000)  # 等待评论内容出现，超时时间为10秒

        # # 确认评论是否加载成功
        # comments = page.locator('.CommentContent')
        # comments_count = await comments.count()
        # print(f"Found {comments_count} comments.")

        # # 输出每个评论的详细信息
        # for i in range(comments_count):
        #     comment = comments.nth(i)
        #     comment_text = await comment.text_content()
        #     print(f"Comment {i+1}: {comment_text}")

        # await page.screenshot(path="debug.png")


        # # 使用 JavaScript 修改 --app-font-size 变量
        # await page.evaluate(f'''() => {{
        #     document.documentElement.style.setProperty('--app-font-size', '30px');
        # }}''')

        # # 检查修改结果
        # font_size = await page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--app-font-size")')
        # print(f"Modified --app-font-size: {font_size}")

        
        # # 获取页面高度
        # page_height = await page.evaluate("document.body.scrollHeight")
        # viewport_height = await page.evaluate("window.innerHeight")
        # print(f"page_height: {page_height}, viewport_height: {viewport_height}")

        # # 定义每次滚动的步长（稍小于视口高度以保留重叠）
        # scroll_step = viewport_height - 250  # 保留100像素的重叠部分

        # # 初始化截图索引
        # screenshot_index = 1
        # output_dir = Path("output") / f'{url_file_name}_{url.split("/")[-1]}'
        # print(f"Output directory: {output_dir}")
        # output_dir.mkdir(parents=True, exist_ok=True)
        # # # 定义截图区域
        # # clip_area = {
        # #     'x': 20,  # 区域的起始点 x 坐标
        # #     'y': 50,  # 区域的起始点 y 坐标
        # #     'width': 670,  # 区域的宽度
        # #     'height': 933  # 区域的高度
        # # }
        # clip_area = None
        # # 控制截图到第一个回答结束。
        # for offset in range(0, page_height, scroll_step):
        #     # to follow dictionary order.
        #     screenshot_path = output_dir / f"{screenshot_index:02}.png"
        #     # 截取截图
        #     await page.screenshot(path=screenshot_path, clip=clip_area)
        #     screenshot_index += 1
        #     # 滚动页面，但确保不超过页面底部
        #     next_offset = min(offset + scroll_step, page_height - viewport_height)
        #     await page.evaluate(f"window.scrollTo(0, {next_offset})")

        # # # Optionally, take a screenshot
        # # await page.screenshot(path="1675707394.png", full_page=True)
        
        # # # Optionally, extract content
        # # content = await page.content()
        # # with open("content.html", "w") as f:
        # #     f.write(content)
        # # print(content)
        
        await browser_context.close()


async def batch_url_to_screenshots(urls, url_file_name=""):
    for url in urls:
        print(f"Start crawling {url}")
        await url_to_screenshots(url, url_file_name)


if __name__ == '__main__':
    asyncio.run(url_to_screenshots("https://www.zhihu.com/question/411985422/answer/2825317069"))
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--url_file", "-i", help="File containing urls to crawl")
    # args = parser.parse_args()
    # with open(args.url_file, "r") as f:
    #     urls = f.read().split("\n")
    # asyncio.run(batch_url_to_screenshots(urls, url_file_name=Path(args.url_file).stem))
