import logging
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
from enum import auto, unique, Enum
from pathlib import Path
from math import prod
from datetime import datetime
from itertools import permutations
from dotenv import dotenv_values
#from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from selectolax.parser import HTMLParser
from tqdm.auto import tqdm


logger = logging.getLogger("nj_biergarten")
# "The call to basicConfig() should come before any calls to a logger’s methods such as debug(), info(), etc."
# Cf. <https://docs.python.org/3/howto/logging.html#logging-to-a-file>
logging.basicConfig()


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
    # TODO: make the downloads dir absolute
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


@unique
class Cracker(Enum):
    TRICK = auto()
    TROCR = auto()


def crack_captcha(
    response: httpx.Response,
    *args,
    cracker: Cracker = Cracker.TRICK,
) -> str:
    if not isinstance(cracker, Cracker):
        raise TypeError(f"Expect Cracker but got {type(cracker) = }")


    tree = HTMLParser(response.content)
    img_node = tree.css_first('img[alt="驗證碼圖片"]')
    if cracker is Cracker.TRICK:
        guess = img_node.attributes["src"].split("=")[-1]
    if cracker is Cracker.TROCR:
        pass

    return guess


def is_reasonable(captcha: str) -> bool:
    return len(captcha) == 6 and captcha.islower() and captcha.isalnum()


def httpx_selectolax_login(
    client: httpx.Client,
    *args,
    cracker: Cracker = Cracker.TRICK,
    max_attempts: int = 3,
)-> None:
    config = dotenv_values(".env")
    login_url = config["LOGIN_URL"]
    post_url = config["POST_URL"]

    data = {
        "acc": config["USERNAME"],
        "pwd": config["PASSWORD"],
    }
    ipdb.set_trace()

    for _ in range(max_attempts):
        response = client.get(login_url)
        guess = crack_captcha(response, cracker=cracker)
        if not is_reasonable(guess):
            continue
        data["chk"] = guess
        post_response = client.post(post_url, data=data)
        if login_succeeded(post_response):
            return

    # TODO: Login failed. Raise exception?
    #raise


def login_succeeded(post_response: httpx.Response) -> bool:
    return "登入成功" in post_response.text


def login_succeeded2(post_response: httpx.Response) -> bool:
    return "chkpas=TRUE" in post_response.headers["set-cookie"]


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
            logger.debug(f"get {image_rel_url}")
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

    logger.info(f"Downloading the remaining {q.qsize() = } images.")
    # Block until all tasks are done.
    q.join()


def slash_join(*args) -> str:
    return "/".join(args)


def queue_image_urls(
    q: queue.Queue,
    *args,
    client: httpx.Client,
    # TODO: cache the not-yet-crawled urls
    #cache: None,
) -> None:
    abs_parent_dir = Path(__file__).parent
    abs_download_dir = abs_parent_dir / "images"
    already_downloaded = { str(p.relative_to(abs_parent_dir)) for p in abs_download_dir.glob("**/*.jpg")}
    #ipdb.set_trace()
    config = dotenv_values(".env")
    website = config["WEBSITE"]
    photo_url = config["PHOTO_URL"]
    response = client.get(photo_url)
    tree = HTMLParser(response.content)
    page_select = tree.css_first('select[class="a00"]')
    num_pages = sum(1 for _ in page_select.iter())

    print(f"{num_pages = }")
    for k in range(1, num_pages + 1):
        response = client.get(f"{photo_url}?page={k}")
        tree = HTMLParser(response.content)
        ul = tree.css_first('ul[class="show_album_list"]')
        lis = ul.css('li')
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
                if not image_rel_url in already_downloaded:
                    q.put(image_rel_url)
                    logger.debug(f"put {image_rel_url}")


def main():
    logger.setLevel(level=logging.DEBUG)
    with httpx.Client() as client:
        httpx_selectolax_login(client)
        threading_download_photos(client)


def main2():
    logger.setLevel(level=logging.INFO)

    print("Stage 1: Collect image urls")
    with httpx.Client() as client:
        httpx_selectolax_login(client)
        q = queue.Queue()
        queue_image_urls(q, client=client)

    print()
    print("Stage 2: Download images")
    config = dotenv_values(".env")
    website = config["WEBSITE"]
    with httpx.Client() as client:
        with tqdm(total=q.qsize()) as pbar:
            while q.qsize() > 0:
                image_rel_url = q.get()
                logger.debug(f"get {image_rel_url}")
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
                pbar.update()


if __name__ == "__main__":
    #main()
    main2()
