import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import tiktoken

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


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

    driver = uc.Chrome(options=options)
    driver.get(url)
    title = driver.title

    html = driver.page_source

    driver.quit()

    soup = BeautifulSoup(html, "lxml").find("body")
    texts = soup.get_text(strip=True)

    return title, texts
