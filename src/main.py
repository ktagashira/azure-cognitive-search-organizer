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
openai.api_version = "2023-06-01-preview"
deployment_name = os.environ["AZURE_OPEN_AI_DEPLOYMENT"]

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

context_output_style = {
    "context": "テキスト",
}
context_output_style = json.dumps(context_output_style, ensure_ascii=False)  # type: ignore

title_category_system_style = {"title": "タイトル", "category": "カテゴリー"}
title_category_system_style = json.dumps(
    title_category_system_style, ensure_ascii=False
)  # type: ignore

title_category_system_prompt = f"""
userの入力はwebサイトからテキストを抽出してきたものです。
このテキストに対するタイトルとカテゴリを考えてください。
# output形式(in JSON)
{title_category_system_style}
"""

max_retries = 5
max_input_size = 7000


def main():
    df = pd.read_csv(os.path.join("data", os.environ["URL_FILE_NAME"]))
    result_cols = ["Index", "URL", "Title", "Category", "Context"]
    results = pd.DataFrame(columns=result_cols)
    client_name = os.environ["CLIENT_NAME"]
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        index = client_name + "_" + str(idx)
        retry_count = 0
        while retry_count < max_retries:
            try:
                time.sleep(5)
                url = row[os.environ["URL_COLUMNS"]]
                title, html_text = extract_html_text(url)
                print("文字サイズ: ", len(html_text))
                print("トークン数: ", encoding.encode(html_text))
                if len(html_text) > max_input_size:
                    html_text = "".join(
                        encoding.decode(encoding.encode(html_text)[:max_input_size])
                    )

                context_system_prompt = f"""
                userの入力は、webサイトのbodyのテキストを抽出してきたものです。
                このテキストを、以下のタイトルに沿ったAzure Cognitive Searchのcontextとして利用できる綺麗な文章に整理してください。
                # タイトル
                { title }
                # 制約条件
                - 500文字以内に収めること。
                - 情報が多いのは良いことなので、情報を削除しすぎないこと。
                # output形式(in JSON)
                {context_output_style}
                """
                context_completion = openai.ChatCompletion.create(
                    engine=deployment_name,
                    temperature=0.4,
                    messages=[
                        {"role": "system", "content": context_system_prompt},
                        {"role": "user", "content": html_text},
                        {"role": "assistant", "content": "{"},
                    ],
                )
                context_response = json.loads(
                    "{" + context_completion.choices[0]["message"]["content"]
                )

                title_category_completion = openai.ChatCompletion.create(
                    engine=deployment_name,
                    temperature=0.4,
                    messages=[
                        {"role": "system", "content": title_category_system_prompt},
                        {"role": "user", "content": html_text},
                        {"role": "assistant", "content": "{"},
                    ],
                )
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
                    columns=result_cols,
                )

                results = pd.concat([results, record], axis=0, ignore_index=True)
                break

            except Exception as e:
                print(e)
                time.sleep(15)
                retry_count += 1
                continue

    results.to_csv(os.path.join("results", client_name + "_output.csv"), index=False)


if __name__ == "__main__":
    main()
