"""
@File    :   refine.py
@Time    :   2023/12/07 20:16:46
@Author  :   TankNee
@Version :   1.0
@Desc    :   修饰优化字幕
"""

import argparse
import glob
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

from tqdm import tqdm

from common import read_json, retry

SYSTEM_PROMPT = """你的任务是把用户输入转换为更加流畅自然的表达形式，用户的输入是一场英雄联盟职业比赛的解说词片段，每一行代表一句话，可能是不同的人说的，也可能是同一个人说的，解说词中包含许多英雄联盟专业用语，你需要保留这些特殊用词，也有一些可能是语音识别错误的词语，你需要进行修正，你的输出不能过于书面化，要贴近解说词的真实含义，必要时你可以丢弃部分解说词中表达不完整的内容，不能过于啰嗦，要适当精简。直接输出解说词内容，不要有其他的无关内容。
"""

USER_PROMPT = """下面是这场比赛的解说词：
{subtitle_text}"""


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--subtitle_dir",
        type=str,
        default="subtitles",
    )
    parser.add_argument(
        "--video_dir",
        type=str,
        default="/new_disk/cv_group/tanknee/Data/lpl-gpt/2023-spring-split/videos",
    )
    parser.add_argument("--output_path", type=str, default="outputs/results.jsonl")

    return parser.parse_args()

@retry(retry_times=3)
def refine_subtitle(client: OpenAI, subtitle_text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": USER_PROMPT.format(subtitle_text=subtitle_text),
            },
        ],
        seed=2023,
        temperature=0.1,
        max_tokens=512,
    )
    return response.choices[0].message.content


def main():
    args = get_args()
    load_dotenv()
    openai_client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )

    subtitles = glob.glob(os.path.join(args.subtitle_dir, "*.json"))
    subtitles.sort()
    with open(args.output_path, "a+") as f:
        f.seek(0)
        results = [json.loads(line) for line in f]
        f.seek(0, 2)
        for subtitle_path in tqdm(subtitles):
            if any([r["subtitle_path"] == subtitle_path for r in results]):
                continue
            video_path = subtitle_path.replace("subtitles", "videos").replace("json", "mp4")
            subtitle = read_json(subtitle_path)
            subtitle_text = "\n".join([s["text"] for s in subtitle])
            refined_subtitle = refine_subtitle(openai_client, subtitle_text)
            results.append(
                {
                    "video_path": video_path,
                    "subtitle_path": subtitle_path,
                    "subtitle": subtitle_text,
                    "refined_subtitle": refined_subtitle,
                }
            )
            f.write(
                json.dumps(
                    {
                        "video_path": video_path,
                        "subtitle_path": subtitle_path,
                        "subtitle": subtitle_text,
                        "refined_subtitle": refined_subtitle,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            f.flush()
    return


if __name__ == "__main__":
    main()
