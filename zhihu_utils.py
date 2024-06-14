import os
import zipfile
import shutil

# Config
WEB_SOCKET_DEBUGGER_URL = "ws://localhost:9222/devtools/browser/51c1de44-dc33-4e58-ba5c-8bc45236db18"
VIEWPORT = {"width": 1000, "height": 1013}
FONT_SIZE = "30px"
ANSWER_CLIP_AREA = {
    'x': 20,  # 区域的起始点 x 坐标
    'y': 70,  # 区域的起始点 y 坐标
    'width': 670,  # 区域的宽度
    'height': 883  # 区域的高度
}
TOPIC_CLIP_AREA = {
    'x': 155,  # 区域的起始点 x 坐标
    'y': 70,  # 区域的起始点 y 坐标
    'width': 690,  # 区域的宽度
    'height': 885  # 区域的高度
}


async def login_by_cookies(browser_context, cookie_str):
    from tools import utils

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
        # feat issue #14
        # we will save login state to avoid login every time
        user_data_dir = os.path.join(os.getcwd(), "zhihu_browser_data")  # type: ignore
        browser_context = await chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            accept_downloads=True,
            headless=headless,
            proxy=playwright_proxy,  # type: ignore
            # 3:4
            viewport=VIEWPORT,
            user_agent=user_agent
        )
        return browser_context
    else:
        browser = await chromium.launch(headless=headless, proxy=playwright_proxy)  # type: ignore
        browser_context = await browser.new_context(
            viewport=VIEWPORT,
            user_agent=user_agent
        )
        return browser_context


async def connect_existing_browser(chromium):
    # 连接到已经打开的浏览器实例
    browser = await chromium.connect_over_cdp(WEB_SOCKET_DEBUGGER_URL)
    browser_context = browser.contexts[0]
    # 获取现有页面并设置视口
    page = browser_context.pages[0]
    await page.set_viewport_size(VIEWPORT)
    return browser_context


async def modify_font(page):
    # 使用 JavaScript 修改 --app-font-size 变量
    await page.evaluate(f'''() => {{
        document.documentElement.style.setProperty('--app-font-size', '{FONT_SIZE}');
    }}''')
    # # 检查修改结果
    # font_size = await page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--app-font-size")')
    # print(f"Modified --app-font-size: {font_size}")


async def open_comment(page):
    # 滚动到 "更多回答" 附近
    # print('Scrolling to the "更多回答" section...')
    more_answers_header = page.locator('h4.List-headerText:has-text("更多回答")')
    await more_answers_header.scroll_into_view_if_needed()
    await page.wait_for_timeout(500)  # 等待0.5秒
    # 使用更精确的 CSS 选择器定位所有包含“条评论”的按钮
    await page.wait_for_selector('button:has-text("条评论")')
    comment_buttons = page.locator('button:has-text("条评论")')
    
    # 获取按钮数量以便调试
    count = await comment_buttons.count()
    # print(f"Found {count} comment buttons.")

    if count < 2:
        print("Less than 2 comment buttons found. Exiting.")
        return

    # 模拟鼠标移动到按钮并点击
    # print("Hovering over the second comment button...")
    button = comment_buttons.nth(1)
    await button.hover()
    await page.wait_for_timeout(500)  # 等待0.5秒

    # print("Clicking the second comment button...")
    await button.click()
    # print("Second comment button clicked.")
    await page.wait_for_selector('.CommentContent', timeout=10000)  # 等待评论内容出现，超时时间为10秒


async def get_end_position(page, url_type):
    if url_type == "answer":
        # 获取 "更多回答" 元素的位置
        # print('Calculating height from top of the page to the "更多回答" section...')
        more_answers_header_locator = page.locator('h4.List-headerText:has-text("更多回答")')
        more_answers_header_position = int(await more_answers_header_locator.evaluate(
            'element => element.getBoundingClientRect().top + window.scrollY'
        ))
        # print(f'The height from the top of the page to the "更多回答" section is: {more_answers_header_position}px.')
        return more_answers_header_position - 20
    elif url_type == "topic":
        # 获取 "推荐阅读" 元素的位置
        recommendations_header_locator = page.locator('h3.BlockTitle.Recommendations-BlockTitle:has-text("推荐阅读")')        
        recommendations_header_position = int(await recommendations_header_locator.evaluate(
            'element => element.getBoundingClientRect().top + window.scrollY'
        ))
        # print(f'The height from the top of the page to the "推荐阅读" section is: {recommendations_header_position}px.')
        return recommendations_header_position - 30

async def scroll_and_screenshot(page, output_dir, url_type="answer"):
    # url_type: "answer" or "topic"
    
    # 获取视口高度
    viewport_height = await page.evaluate("window.innerHeight")
    # print(f"viewport_height: {viewport_height}")
    
    # 定义每次滚动的步长（稍小于视口高度以保留重叠）
    scroll_step = viewport_height - 200
    
    # 初始化截图索引
    screenshot_index = 1
    output_dir.mkdir(parents=True, exist_ok=True)
    end_position = await get_end_position(page, url_type)
    clip_area = get_clip_area(url_type)
    # 滚动到页面顶部
    await page.evaluate(f"window.scrollTo(0, 0)")

    # 截图并滚动到 "更多回答" 附近
    for offset in range(0, end_position - viewport_height, scroll_step):
        # to follow dictionary order.
        screenshot_path = output_dir / f"{screenshot_index:02}.png"
        
        # 截取截图
        await page.screenshot(path=screenshot_path, clip=clip_area)
        screenshot_index += 1
        await page.evaluate(f"window.scrollTo(0, {offset + scroll_step})")


def make_zip(screenshots_dir, zip_dir):
    # Create a zip file of all png files in the current directory
    zip_file_name = f'{screenshots_dir.name}.zip'
    with zipfile.ZipFile(screenshots_dir / zip_file_name, 'w') as zipf:
        for file_path in screenshots_dir.glob('*.png'):
            # print(f"Adding {file_path} to zip file...")
            zipf.write(file_path, file_path.name)
    # print(f"All PNG files have been added to {zip_file_name}")
    # Ensure the output/zip directory exists
    zip_dir.mkdir(parents=True, exist_ok=True)
    # Move the zip file to the output/zip directory
    shutil.move(str(screenshots_dir / zip_file_name), str(zip_dir / zip_file_name))


def get_url_type(url):
    if "zhuanlan.zhihu.com/p/" in url:
        return "topic"
    elif "www.zhihu.com/question/" in url and "answer" in url:
        return "answer"
    else:
        return "unknown"


def get_clip_area(url_type):
    # 定义截图区域
    if url_type == "answer":
        clip_area = ANSWER_CLIP_AREA
    elif url_type == "topic":
        clip_area = TOPIC_CLIP_AREA
    else:
        clip_area = None
    return clip_area
