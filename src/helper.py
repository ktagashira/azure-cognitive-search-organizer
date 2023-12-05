from logging import getLogger

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import tiktoken

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

logger = getLogger(__name__)


def extract_html_text(url):
    """
    urlからテキストを取得する

    Parameters
    ----------
    url : str
        スクレイピングするURL

    Returns
    -------
    tuple[str, str]
        スクレイピングしたタイトルとテキスト
    """
    options = uc.ChromeOptions()

    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--disk-cache-size=200000000")

    driver = uc.Chrome(options=options)
    driver.set_window_size(950, 800)
    driver.implicitly_wait(10)

    driver.get(url)

    html = driver.page_source
    driver.quit()

    title = BeautifulSoup(html, "lxml").find("title").get_text(strip=True)
    soup = BeautifulSoup(html, "lxml").find("body")

    try:
        texts = soup.get_text(strip=True)
        return title, texts
    except:
        return title, ""
