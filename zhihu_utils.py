from tools import utils
import os

# Config
WEB_SOCKET_DEBUGGER_URL = "ws://localhost:9222/devtools/browser/ef5f8d38-b1a3-427e-9e5f-cb0b5f9d8715"
VIEWPORT = {"width": 700, "height": 1033}
DEVICE_SCALE_FACTOR = 4
FONT_SIZE = "30px"
ANSWER_CLIP_AREA = {
    'x': 20,  # 区域的起始点 x 坐标
    'y': 50,  # 区域的起始点 y 坐标
    'width': 670,  # 区域的宽度
    'height': 933  # 区域的高度
}
# TOPIC_CLIP_AREA


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
            device_scale_factor=DEVICE_SCALE_FACTOR,
            user_agent=user_agent
        )
        return browser_context
    else:
        browser = await chromium.launch(headless=headless, proxy=playwright_proxy)  # type: ignore
        browser_context = await browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=DEVICE_SCALE_FACTOR,
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
    await page.emulate_media({'deviceScaleFactor': DEVICE_SCALE_FACTOR})
    return browser_context


async def modify_font(page):
    # 使用 JavaScript 修改 --app-font-size 变量
    await page.evaluate(f'''() => {{
        document.documentElement.style.setProperty('--app-font-size', '{FONT_SIZE}');
    }}''')
    # # 检查修改结果
    # font_size = await page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--app-font-size")')
    # print(f"Modified --app-font-size: {font_size}")


async def scroll_and_screenshot(page, output_dir, url_type="answer", prefix="answer"):
    # url_type: "answer" or "topic"
    # prefix: "answer" or "comment"
    # 获取页面高度
    page_height = await page.evaluate("document.body.scrollHeight")
    viewport_height = await page.evaluate("window.innerHeight")
    print(f"page_height: {page_height}, viewport_height: {viewport_height}")

    # 定义每次滚动的步长（稍小于视口高度以保留重叠）
    scroll_step = viewport_height - 250  # 保留100像素的重叠部分

    # 初始化截图索引
    screenshot_index = 1
    output_dir.mkdir(parents=True, exist_ok=True)
    # 定义截图区域
    clip_area = ANSWER_CLIP_AREA if url_type == "answer" else None
    # TODO: 控制截图到第一个回答结束。
    for offset in range(0, page_height, scroll_step):
        # to follow dictionary order.
        screenshot_path = output_dir / f"{prefix}_{screenshot_index:02}.png"
        # 截取截图
        await page.screenshot(path=screenshot_path, clip=clip_area)
        screenshot_index += 1
        # 滚动页面，但确保不超过页面底部
        next_offset = min(offset + scroll_step, page_height - viewport_height)
        await page.evaluate(f"window.scrollTo(0, {next_offset})")


async def open_comment(page):
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
    await page.wait_for_timeout(500)  # 等待0.5秒

    print("Clicking the second comment button...")
    await button.click()
    print("Second comment button clicked.")
    await page.wait_for_selector('.CommentContent', timeout=10000)  # 等待评论内容出现，超时时间为10秒
