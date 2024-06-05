from main import crawl
import asyncio

import pandas as pd
from datetime import datetime
from pathlib import Path

def merge_search_results(keyword, newly_scraped_file_name):
    # 设置文件路径
    base_dir = "data/xhs-merged"
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    final_file = Path(base_dir) / f"{keyword}_merged_search_results.csv"
    new_data = pd.read_csv(newly_scraped_file_name)
    new_data['register_date'] = datetime.now().strftime("%Y-%m-%d")
    if final_file.exists():
        final_data = pd.read_csv(final_file)
        merged_data = pd.concat([final_data, new_data]).drop_duplicates(subset="note_id").reset_index(drop=True)
    else:
        merged_data = new_data

    # 保存合并后的数据
    merged_data.to_csv(final_file, index=False)
    print(f"Merged data {newly_scraped_file_name} to {final_file}")


def per_keyword_crawl(keyword):
    newly_scraped_file_name = asyncio.run(crawl(keywords=keyword))
    print(f"Crawled data for {keyword} to {newly_scraped_file_name}")
    merge_search_results(keyword, newly_scraped_file_name)


if __name__ == '__main__':
    keywords = ["prompt"]
    for keyword in keywords:
        print(f"Crawling data for {keyword} ...")
        per_keyword_crawl(keyword)
