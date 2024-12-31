import threading
import queue
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


def crazy_infinite_practical_captcha_download(
    num_images: int = 1_000_000,
    *args,
    # 0 and o's diff are hardly noticeable
    symbols: str =  string.ascii_lowercase + string.digits[1:],
    save_dir: str | Path = Path.cwd() / "downloads",
) -> None:
    try:
        collect_practical_train_data(
            num_images,
            symbols=symbols,
            save_dir=save_dir,
        )
    except:
        collect_practical_train_data(
            num_images,
            symbols=symbols,
            save_dir=save_dir,
        )


def selenium_login():
    pass


def nodriver_login():
    pass


def httpx_selectolax_login(client: httpx.Client)-> None:
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


def download_image(
    image_url: str,
    *args,
    save_to: Path,
    client: httpx.Client,
) -> None:
    if save_to.is_file():
        return None

    response = client.get(image_url)
    image_bytes = response.content
    with open(save_to, "wb") as f:
        f.write(image_bytes)


def threading_download_photos(
    client: httpx.Client,
) -> None:
    q = queue.Queue()
    config = dotenv_values(".env")
    website = config["WEBSITE"]

    def worker():
        while True:
            image_rel_url = q.get()
            save_to = Path(image_rel_url)
            save_dir = save_to.parent
            if not save_dir.exists():
                save_dir.mkdir(parents=True, exist_ok=True)
            image_abs_url = slash_join(website, image_rel_url)
            download_image(
                image_abs_url,
                save_to=save_to,
                client=client,
            )
            q.task_done()

    # Turn-on the worker thread.
    threading.Thread(target=worker, daemon=True).start()

    # Populate our queue with urls
    queue_image_urls(q, client=client)
    # TODO: using logging instead?
    print("Crawling... Veuillez patienter, s'il vous plaît.")
    # Block until all tasks are done.
    q.join()


def slash_join(*args) -> str:
    return "/".join(args)


def queue_image_urls(
    q: queue.Queue,
    *args,
    client: httpx.Client,
) -> None:
    config = dotenv_values(".env")
    website = config["WEBSITE"]
    photo_url = config["PHOTO_URL"]
    response = client.get(photo_url)
    tree = HTMLParser(response.content)
    page_select = tree.css_first('select[class="a00"]')
    num_pages = sum(1 for _ in page_select.iter())

    for k in range(1, num_pages + 1):
        response = client.get(f"{photo_url}?page={k}")
        tree = HTMLParser(response.content)
        ul = tree.css_first('ul[class="show_album_list"]')
        lis = ul.css('li')
        # TODO: using logging instead?
        print(f"Page {k}: {len(lis)} albums")
        for li in tqdm(lis):
            div = li.css_first('div[class="swpl2"]')
            anchor = div.css_first('a')
            rel_url = anchor.attributes["href"]
            #upload_date = div.css_first("span").text()
            abs_url = slash_join(website, rel_url)
            response = client.get(abs_url)
            tree = HTMLParser(response.content)
            for figure in tree.css('figure[class="jc_fig"]'):
                anchor = figure.css_first('a')
                image_rel_url = anchor.attributes["href"]
                q.put(image_rel_url)


def main():
    with httpx.Client() as client:
        httpx_selectolax_login(client)
        threading_download_photos(client)


if __name__ == "__main__":
    main()
