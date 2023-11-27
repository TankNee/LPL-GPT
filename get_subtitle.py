#!/usr/bin/env python
# author = 'ZZH'
# time = 2023/11/27
# project = get_subtitle
import argparse
import json
import os

import requests
from dotenv import load_dotenv
from loguru import logger

from common import create_logger, read_jsonl

load_dotenv()


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=str, default="config/records.jsonl")
    parser.add_argument("--output_dir", type=str, default="subtitles")
    return parser.parse_args()


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Cookie": os.getenv("COOKIE"),
}
CID_VID_URL = "http://api.bilibili.com/x/web-interface/view?bvid="
SUBTITLE_URL = "https://api.bilibili.com/x/player/v2?cid=&s&aid=%s&bvid=%s"


def get_cid_vid(bvid: str) -> (str, list):
    """
    :param bvid:
    :return: aid 和 （cid_list 代表每一场信息）
    """
    logger.info(f"cid_vid_url:{CID_VID_URL + bvid}")
    response = requests.get(CID_VID_URL + bvid, headers=headers)
    text = json.loads(response.text)
    aid = text["data"]["aid"]
    cid_list = [d["cid"] for d in text["data"]["pages"]]
    return aid, cid_list


def get_subtitle(cid, aid, bvid) -> dict:
    api_url = "https://api.bilibili.com/x/player/v2?cid=%s&aid=%s&bvid=%s" % (cid, aid, bvid)
    logger.info(f"subtitle_url:{api_url}")
    response = requests.get(
        api_url,
        headers=headers,
    )
    text = json.loads(response.text)
    try:
        subtitle_url = (
                "https:" + text["data"]["subtitle"]["subtitles"][0]["subtitle_url"]
        )
    except Exception:
        logger.error(f"糟糕，subtitle_url没有，对应bvid:{bvid},cid:{cid},aid:{aid}")
        subtitle_url = None
    if not subtitle_url:
        return {}
    response = requests.get(subtitle_url, headers=headers)
    ret_dict = json.loads(response.text)
    return ret_dict


def main(args):
    records = read_jsonl(args.records)
    for d in records:
        bvid = d["url"].split("/")[-2]
        if d["playlist_idx"]:
            playlist_idx = [i - 1 for i in d["playlist_idx"]]  # 下标从0开始
            base_file_name = os.path.join(
                args.output_dir, "_".join(d["teams"]) + "_" + d["date"]
            )
            aid, cid_list = get_cid_vid(bvid)
            for i, idx in enumerate(playlist_idx):
                file_name = base_file_name + "_" + str(i + 1) + ".json"
                subtitle_dict = get_subtitle(cid_list[idx], aid, bvid)
                if not subtitle_dict:
                    logger.error(f"{file_name} 啊哦，没有字幕")
                else:
                    with open(file_name, "w") as f:
                        logger.info(f"正在往{file_name} 写入字幕数据")
                        json.dump(subtitle_dict, f, ensure_ascii=False)


if __name__ == "__main__":
    create_logger(log_file="logs/get_subtitle.log")
    args = get_args()
    logger.debug(args)
    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)
    main(args)
