import os
from logging import getLogger, StreamHandler, Formatter, BASIC_FORMAT, INFO
import openai
import pandas as pd
from tqdm.auto import tqdm
import json
import time

from helper import extract_html_text

logger = getLogger()
handler = StreamHandler()
handler.setLevel(INFO)
handler.setFormatter(Formatter(BASIC_FORMAT))
logger.setLevel(INFO)
logger.addHandler(handler)

openai.api_key = os.environ["AZURE_OPEN_AI_API_KEY"]
openai.api_base = os.environ["AZURE_OPEN_AI_BASE"]
openai.api_type = "azure"
openai.api_version = "2023-05-15"
deployment_name = os.environ["AZURE_OPEN_AI_DEPLOYMENT"]


context_output_style = {
    "context": "[Japanese Organized Text]",
}
context_output_style = json.dumps(context_output_style, ensure_ascii=False)  # type: ignore

title_category_system_style = {"title": "[タイトル]", "category": "[カテゴリー]"}
title_category_system_style = json.dumps(
    title_category_system_style, ensure_ascii=False
)  # type: ignore

title_category_system_prompt = f"""
userの入力はwebサイトからテキストを抽出してきたものです。
このテキストに対するタイトルとカテゴリを考えてください。
# output形式(in JSON)
{title_category_system_style}
"""

SLEEP_TIME = 5
MAX_RETRIES = 5

RESULT_COLS = ["Index", "URL", "Title", "Category", "Context"]


def main():
    if not os.path.exists("results"):
        os.mkdir("results")
    df = pd.read_csv(os.environ["URL_FILE_PATH"])
    client_name = os.environ["CLIENT_NAME"]

    for idx, row in tqdm(df.iterrows(), total=len(df)):
        index = client_name + "_" + str(idx)
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                url = row[os.environ["URL_COLUMNS"]]
                time.sleep(SLEEP_TIME)

                logger.info("%s", f"URL: {url}")
                title, html_text = extract_html_text(url)
                logger.info("%s", f"Title: {title}")

                if type(title) != str:
                    logger.info("%s", "cannot get title.")
                    retry_count += 1
                    continue
                if len(html_text) == 0:
                    logger.info("%s", "cannot get text.")
                    break

                context_system_prompt = f"""
                User input is unclean text extracted from the website.              
                Please clean the text in a format that can be used as Content for Azure Cognitive Search.
                
                # Rules
                1. The output must be clean Japanese sentences. Clean Japanese is that for which punctuation marks such as 「。」 or 「、」 are used correctly.
                2. If there are any addresses or phone numbers in the text, please prioritize extracting them.
                3. 次の情報を必ず出力に入れてください。
                    i. 商品名
                    ii. 商品情報(原産国や農園など)
                    iii. 商品に関連する情報
                4. 情報を削除しすぎてはいけません。
                5. 以上のルールを守らない場合は、Organizationは無効になります。
                
                # Output Format(in JSON)
                { context_output_style }
                """

                context_completion = openai.ChatCompletion.create(
                    engine=deployment_name,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": context_system_prompt},
                        {"role": "user", "content": html_text},
                    ],
                    response_format={"type": "json_object"},
                    timeout=60,
                )
                res = (
                    context_completion.choices[0]["message"]["content"]
                    .replace(" ", "")
                    .replace("\n", "")
                )
                logger.info("%s", f"Context: {res}")
                context_response = json.loads(res)

                title_category_completion = openai.ChatCompletion.create(
                    engine=deployment_name,
                    temperature=0.4,
                    messages=[
                        {"role": "system", "content": title_category_system_prompt},
                        {"role": "user", "content": context_response["context"]},
                    ],
                    response_format={"type": "json_object"},
                )
                res = title_category_completion.choices[0]["message"]["content"]

                logger.info("%s", f"Title & Category: {res}")
                title_category_response = json.loads(
                    title_category_completion.choices[0]["message"]["content"]
                )
                record = pd.DataFrame(
                    [
                        [
                            index,
                            url,
                            title,
                            title_category_response["category"],
                            context_response["context"],
                        ]
                    ],
                    columns=RESULT_COLS,
                )

                record.to_csv(
                    os.path.join("results", client_name + "_output.csv"),
                    index=False,
                    mode="a",
                    header=False,
                )
                break

            except Exception as e:
                logger.info(e)
                retry_count += 1
                continue


if __name__ == "__main__":
    main()
