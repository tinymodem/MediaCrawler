import asyncio
from playwright.async_api import async_playwright

from pathlib import Path
import argparse
from zhihu_utils import (launch_browser, connect_existing_browser, login_by_cookies,
modify_font, scroll_and_screenshot, open_comment, make_zip)


async def process_one_url(url, output_dir, init_browser_mode="connect"):
    # init_browser_mode: "launch" or "connect". Crawling comments requires connect mode.
    async with async_playwright() as p:
        if init_browser_mode == "launch":
            from tools import utils

            browser_context = await launch_browser(p.chromium, None, utils.get_user_agent(), headless=True, save_login_state=True)
            with open("cookies.txt", "r") as f:
                cookie_str = f.read()
            await login_by_cookies(browser_context, cookie_str)
            page = await browser_context.new_page()
        elif init_browser_mode == "connect":
            browser_context = await connect_existing_browser(p.chromium)
            page = browser_context.pages[0]
            await page.bring_to_front()
        else:
            raise ValueError(f"Invalid init_browser_mode: {init_browser_mode}")
        
        await page.goto(url)
        # print(f'Before opening comment, page height {await page.evaluate("document.body.scrollHeight")}')
        # await scroll_and_screenshot(page, output_dir)
        if init_browser_mode == "connect":
            await open_comment(page)
        await modify_font(page)
        # print(f'After opening comment, page height {await page.evaluate("document.body.scrollHeight")}')
        await scroll_and_screenshot(page, output_dir)
        make_zip(output_dir, output_dir.parent / "zip")
        await browser_context.close()


async def process_url_file(input_file, output_dir):
    with open(input_file, "r") as f:
        urls = f.read().split("\n")
    for i, url in enumerate(urls):
        print(f"Start crawling {i}: {url}")
        output_dir_of_one_url = output_dir / Path(input_file).stem / url.split("/")[-1]
        output_dir_of_one_url.mkdir(parents=True, exist_ok=True)
        await process_one_url(url, output_dir_of_one_url)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--url_file", "-i", help="File containing urls to crawl")
    parser.add_argument("--output_dir", "-o", default="output", help="Output directory")
    args = parser.parse_args()
    asyncio.run(process_url_file(args.url_file, Path(args.output_dir)))
