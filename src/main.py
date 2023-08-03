import os
import openai
import pandas as pd
import tiktoken
from tqdm.auto import tqdm
import json
import time

from helper import extract_html_text

openai.api_key = os.environ["AZURE_OPEN_AI_API_KEY"]
openai.api_base = os.environ["AZURE_OPEN_AI_BASE"]
openai.api_type = "azure"
openai.api_version = "2023-07-01-preview"
deployment_name = os.environ["AZURE_OPEN_AI_DEPLOYMENT"]

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-16k")

context_output_style = {
    "context": "[Japanese Summarized Text up to 1000 characters]",
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

SLEEP_TIME = 10
MAX_RETRIES = 5
MAX_INPUT_SIZE = 8000
MAX_CONTEXT_LENGTH = 1000

RESULT_COLS = ["Index", "URL", "Title", "Category", "Context"]


def main():
    df = pd.read_csv(os.environ["URL_FILE_PATH"])
    client_name = os.environ["CLIENT_NAME"]

    for idx, row in tqdm(df.iterrows(), total=len(df)):
        index = client_name + "_" + str(idx)
        print("Index: ", index)
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                time.sleep(SLEEP_TIME)
                url = row[os.environ["URL_COLUMNS"]]
                print("URL: ", url)
                title, html_text = extract_html_text(url)
                print("タイトル: ", title)
                if len(html_text) > MAX_INPUT_SIZE:
                    html_text = "".join(
                        encoding.decode(encoding.encode(html_text)[:MAX_INPUT_SIZE])
                    )
                print("トークン数: ", len(encoding.encode(html_text)))

                context_system_prompt = f"""
                User input is text extracted from the website.              
                Summarize the text into five clean Japanese sentences of no more than {MAX_CONTEXT_LENGTH} tokens according to the Title.
                # Title
                {title}
                
                # Rules
                1. The text must be organized into five clean Japanese sentences.
                2. The text must be no more than 1000 tokens.

                # Output Format(in JSON)
                { context_output_style }
                """

                context_completion = openai.ChatCompletion.create(
                    engine=deployment_name,
                    temperature=0.4,
                    messages=[
                        {"role": "system", "content": context_system_prompt},
                        {"role": "user", "content": html_text},
                        {"role": "assistant", "content": "{"},
                    ],
                    timeout=60,
                )
                res = (
                    context_completion.choices[0]["message"]["content"]
                    .replace("\n", "")
                    .replace(" ", "")
                )
                if res[-1] != "}":
                    res += "}"
                if res[-2] != '"':
                    res = res[:-1] + '"}'
                print(res)
                context_response = json.loads("{" + res)

                title_category_completion = openai.ChatCompletion.create(
                    engine=deployment_name,
                    temperature=0.4,
                    messages=[
                        {"role": "system", "content": title_category_system_prompt},
                        {"role": "user", "content": context_response["context"]},
                        {"role": "assistant", "content": "{"},
                    ],
                )
                res = title_category_completion.choices[0]["message"]["content"]
                if res[-1] != "}":
                    res += "}"
                print(res)
                title_category_response = json.loads(
                    "{" + title_category_completion.choices[0]["message"]["content"]
                )
                record = pd.DataFrame(
                    [
                        [
                            index,
                            url,
                            title_category_response["title"],
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
                print(e)
                time.sleep(10)
                retry_count += 1
                continue


if __name__ == "__main__":
    main()
