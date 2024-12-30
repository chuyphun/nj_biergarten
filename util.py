import asyncio
import random
import httpx
import time
import ipdb
import string
import asyncio
import aiofiles
from pathlib import Path
from math import prod
from datetime import datetime
from itertools import permutations
from dotenv import dotenv_values
#from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from selectolax.parser import HTMLParser
from tqdm.auto import tqdm


class TrOCREngine:
    def __init__(self):
        pass

    def solve_captcha(self):
        pass


def data_size(num_images: int) -> int:
    image_size_in_KB = 4
    data_size_in_GB = (num_images * image_size_in_KB) // 10**6
    return data_size_in_GB


def train_data_size(
    *args,
    num_symbols: int = 35,
    length: int = 6,
):
    """
    35 comes from len(string.ascii_lowercase + string.digits[1:])
    """
    num_images = num_symbols ** length
    data_size_in_GB = data_size(num_images)
    data_size_in_TB = data_size_in_GB // 1_000
    return data_size_in_TB


def collect_almost_all_train_data(
    *args,
    # 0 and o's diff are hardly noticeable
    symbols: str =  string.ascii_lowercase + string.digits[1:],
    captcha_length: int = 6,
    save_dir: str | Path = Path.cwd() / "downloads",
) -> None:
    config = dotenv_values(".env")
    captcha_servers = [config["PARENT_CAPTCHA_SERVER"],
                       config["TEACHER_CAPTCHA_SERVER"]]
    total = symbols ** captcha_length
    with httpx.Client() as client:
        for t in tqdm(product(symbols, repeat=captcha_length), total=total):
            captcha = "".join(t)
            captcha_server = random.choice(captcha_servers)
            url = f"{captcha_server}{captcha}"
            response = client.get(url)
            now = datetime.now().isoformat()
            file_path = save_dir / f"{now}_{captcha}.jpg"
            with open(file_path, "wb") as f:
                f.write(response.content)


def collect_practical_train_data(
    num_images: int = 1_000_000,
    *args,
    # 0 and o's diff are hardly noticeable
    symbols: str =  string.ascii_lowercase + string.digits[1:],
    save_dir: str | Path = Path.cwd() / "downloads",
) -> None:
    # 1 million images ~ 4 GB
    config = dotenv_values(".env")
    captcha_servers = [config["PARENT_CAPTCHA_SERVER"],
                       config["TEACHER_CAPTCHA_SERVER"]]
    save_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client() as client:
        for _ in tqdm(range(num_images)):
            captcha = "".join(random.choices(symbols, k=6))
            captcha_server = random.choice(captcha_servers)
            url = f"{captcha_server}{captcha}"
            response = client.get(url)
            now = datetime.now().isoformat()
            file_path = save_dir / f"{now}_{captcha}.jpg"
            with open(file_path, "wb") as f:
                f.write(response.content)


def selenium_login():
    pass


def nodriver_login():
    pass


def httpx_selectolax_login(client: httpx.Client):
    config = dotenv_values(".env")
    login_url = config["LOGIN_URL"]
    post_url = config["POST_URL"]

    response = client.get(login_url)
    tree = HTMLParser(response.content)
    captcha_img = tree.css_first('img[alt="驗證碼圖片"]')
    captcha_groundtruth = captcha_img.attributes["src"].split("=")[-1]
    #ipdb.set_trace()

    data = {
        "acc": config["USERNAME"],
        "pwd": config["PASSWORD"],
        "chk" : captcha_groundtruth,
    }
    post_response = client.post(post_url, data=data)


def main():
    with httpx.Client() as client:
        httpx_selectolax_login(client)



if __name__ == "__main__":
    main()
