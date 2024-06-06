import requests
from pathlib import Path
import json


def ocr(file_path, url="http://localhost:18001/api/ocr/"):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
    return response.text


def contains_phrase(data, phrase):
    """
    Check if the given phrase is present in the JSON data.

    Parameters:
    data (dict): The JSON data as a dictionary.
    phrase (str): The phrase to search for.

    Returns:
    bool: True if the phrase is found, False otherwise.
    """
    for outer_list in data.get('result', []):
        for inner_list in outer_list:
            if isinstance(inner_list, list) and len(inner_list) == 2:
                if phrase == inner_list[1][0]:
                    return True
    return False


def should_truncate(file_index, truncate_index):
    return truncate_index > -1 and file_index >= truncate_index


def filter_more_answers(screenshots_dir):
    truncate_index = -1
    (screenshots_dir / "truncated").mkdir(parents=True, exist_ok=True)
    for file_path in screenshots_dir.glob('*.png'):
        print(f"Checking {file_path} for more answers...")
        file_path_index = int(file_path.stem)
        if should_truncate(file_path_index, truncate_index):
            print(f"Moving {file_path} to truncated directory...")
            file_path.rename(screenshots_dir / "truncated" / file_path.name)
            continue
        if contains_phrase(json.loads(ocr(file_path)), "更多回答"):
            truncate_index = int(file_path.stem)
            print(f"Found more answers at index {truncate_index}. Truncating...")
            file_path.rename(screenshots_dir / "truncated" / file_path.name)


if __name__ == '__main__':
    screenshots_path = Path('./output/1675707394/')
    filter_more_answers(screenshots_path)
