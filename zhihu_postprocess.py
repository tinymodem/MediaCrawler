import requests
from pathlib import Path
import json
import zipfile
import shutil


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

    # Create a zip file of all png files in the current directory
    zip_file_name = f'{screenshots_dir.name}.zip'
    with zipfile.ZipFile(screenshots_dir / zip_file_name, 'w') as zipf:
        for file_path in screenshots_dir.glob('*.png'):
            print(f"Adding {file_path} to zip file...")
            zipf.write(file_path, file_path.name)
    print(f"All PNG files have been added to {zip_file_name}")

    # Ensure the output/zip directory exists
    output_zip_dir = Path('./output/zip')
    output_zip_dir.mkdir(parents=True, exist_ok=True)
    
    # Move the zip file to the output/zip directory
    shutil.move(str(screenshots_dir / zip_file_name), str(output_zip_dir / zip_file_name))


def batch_filter_more_answers(screenshots_dir):
    for screenshots_subdir in screenshots_dir.iterdir():
        if screenshots_subdir.is_dir():
            filter_more_answers(screenshots_subdir)
            print(f"Filtered more answers for {screenshots_subdir.name}")


if __name__ == '__main__':
    # screenshots_path = Path('./output/18050858/')
    # filter_more_answers(screenshots_path)
    batch_filter_more_answers(Path('./output/'))
