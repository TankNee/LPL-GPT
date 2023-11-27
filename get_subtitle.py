#!/usr/bin/env python
# author = 'ZZH'
# time = 2023/11/27
# project = get_subtitle
import argparse
import os
import time

import requests
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm

from common import create_logger, read_jsonl, retry, write_json

load_dotenv()


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=str, default="config/records-1.jsonl")
    parser.add_argument("--output_dir", type=str, default="subtitles")
    return parser.parse_args()


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Cookie": os.getenv("COOKIE"),
}
CID_VID_URL = "http://api.bilibili.com/x/web-interface/view?bvid="
SUBTITLE_URL = "https://api.bilibili.com/x/player/v2?cid=&s&aid=%s&bvid=%s"

@retry(5)
def get_cid_vid(bvid: str) -> (str, list):
    """
    :param bvid:
    :return: aid 和 （cid_list 代表每一场信息）
    """
    response = requests.get(CID_VID_URL + bvid, headers=headers)
    text = response.json()
    aid = text["data"]["aid"]
    cid_list = [d["cid"] for d in text["data"]["pages"]]
    return aid, cid_list

@retry(5)
def get_subtitle(cid, aid, bvid) -> dict:
    response = requests.get(
        "https://api.bilibili.com/x/player/v2?cid=%s&aid=%s&bvid=%s" % (cid, aid, bvid),
        headers=headers,
    )
    text = response.json()
    try:
        subtitle_url = (
            "https:" + text["data"]["subtitle"]["subtitles"][0]["subtitle_url"]
        )
    except KeyError:
        logger.error(f"糟糕，subtitle_url没有，对应bvid:{bvid},cid:{cid},aid:{aid}")
        subtitle_url = None
    response = requests.get(subtitle_url, headers=headers)
    ret_dict = response.json()
    return ret_dict


def main(args):
    records = read_jsonl(args.records)
    for d in tqdm(records):
        bvid = d["url"].split("/")[-2]
        if d["playlist_idx"]:
            playlist_idx = [i - 1 for i in d["playlist_idx"]]  # 下标从0开始
            base_file_name = os.path.join(
                args.output_dir, "_".join(d["teams"]) + "_" + d["date"]
            )
            aid, cid_list = get_cid_vid(bvid)
            for i, idx in enumerate(playlist_idx):
                file_name = base_file_name + "_" + str(i + 1) + ".json"
                if os.path.exists(file_name):
                    logger.info(f"{file_name}已经存在，跳过")
                    continue
                subtitle_dict = get_subtitle(cid_list[idx], aid, bvid)
                write_json(file_name, subtitle_dict)
                # 五秒进度条
                for _ in tqdm(range(5)):
                    time.sleep(1)


if __name__ == "__main__":
    create_logger(log_file="logs/get_subtitle.log")
    args = get_args()
    logger.debug(args)
    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)
    main(args)
