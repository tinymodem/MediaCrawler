import requests
from pathlib import Path
import json
import zipfile
import shutil
from datetime import datetime
from zhihu_postprocess import ocr


def publish(
        title,
        content,
        tags,
        images,
        platform="xhs",
        account="baby",
        publishTime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        isPublic=False,
        url="http://123.116.117.39:1681/api/publish"):
    postData = {
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
        response = requests.post(url, data=postData)
        response.raise_for_status()  # Raise an error for bad status codes
        print('Article published successfully!')
    except requests.exceptions.RequestException as error:
        print('Error publishing article:', error)
    return response.json()


def get_first_text(screenshot_path):
    try:
        return json.loads(ocr(screenshot_path / "01.png"))["result"][0][1][0]
    except:
        return ""


def publish_one_note(screenshot_path):
    first_text = get_first_text(screenshot_path)
    publish(
        title=first_text,
        content=first_text,
        tags=",".join(["育儿"]),
        images=",".join([str(p) for p in screenshot_path.glob("*.png")])
    )


if __name__ == '__main__':
    publish_one_note(Path("./output/2193454318"))
