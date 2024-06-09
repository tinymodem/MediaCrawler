import requests
from pathlib import Path
import json
import zipfile
import shutil
from datetime import datetime, timedelta, timezone
from zhihu_postprocess import ocr


def publish(
        title,
        content,
        tags,
        images,
        publishTime,
        platform="xhs",
        account="baby",
        isPublic=False,
        url="http://123.116.117.39:1681/api/publish"):
    post_data = {
        'title': title,
        'content': content,
        'tags': ','.join(tags),
        'images': ','.join(images),
        'platform': platform,
        'account': account,
        'publishTime': publishTime,
        'visibility': 'public' if isPublic else 'private'
    }

    try:
        print(f"posting data: {post_data}")
        response = requests.post(url, data=post_data)
        response.raise_for_status()  # Raise an error for bad status codes
        print('Article published successfully!')
    except requests.exceptions.RequestException as error:
        print('Error publishing article:', error)
    return response.json()


def publish_one_note(text, screenshot_path):
    cst_cn_offset = timezone(timedelta(hours=8))
    # Get the current UTC time
    current_time_utc = datetime.now(timezone.utc)
    current_time_cst_cn = current_time_utc.replace(tzinfo=timezone.utc).astimezone(cst_cn_offset)
    publish(
        title=text,
        content=text,
        tags=["育儿", "育儿知识"],
        images=[str(p) for p in screenshot_path.glob("*.png")],
        publishTime=current_time_cst_cn.strftime('%Y-%m-%dT%H:%M:%S')
    )


if __name__ == '__main__':
    text = "到底应该如何培养一个优秀的小孩？"
    publish_one_note(text, Path("./output/2193454318"))
