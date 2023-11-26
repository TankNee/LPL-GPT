import argparse
import functools
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
import time

from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm


def create_logger():
    logger.add(
        "./logs/download.log",
        level="DEBUG",
        rotation="10 MB",
        compression="zip",
    )


def retry(retry_times, default=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(retry_times):
                try:
                    output = func(*args, **kwargs)
                    return output if output is not None else default
                except Exception as e:
                    logger.warning(f"Function execution failed, retrying... {e}")
                    time.sleep(30)

            raise Exception("Function execution failed after multiple retries.")

        return wrapper

    return decorator


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_list", type=str, default="video_list.json")
    parser.add_argument("--record_file", type=str, default="./config/records.jsonl")
    parser.add_argument("--output_dir", type=str, default="videos")
    return parser.parse_args()


@retry(retry_times=5)
def download(video_url: str, file_name: str, output_dir: str):
    you_get_path = shutil.which("you-get")
    if you_get_path is None:
        raise FileNotFoundError("you-get not found.")

    command = f"{you_get_path} --format=dash-flv480 --no-caption --output-filename {file_name} --output-dir {output_dir} {video_url}"
    subprocess.run(command, shell=True, check=True)


def extract_teams_and_date(text):
    pattern = r"(\d{1,2}月\d{1,2}日).*\s([A-Za-z]+)\svs\s([A-Za-z]+)"
    matches = re.findall(pattern, text)
    if matches:
        match = matches[0]
        date = match[0]
        team1 = match[1]
        team2 = match[2]
        # date变成日期对象
        date = date.replace("月", "-").replace("日", "")
        date = datetime.strptime("2023-" + date, "%Y-%m-%d").date()
        # date变成20230415这样的数字
        date = date.strftime("%Y%m%d")
        return [team1, team2], date
    else:
        return None, None


def has_match(string: str) -> bool:
    pattern = r"第[一二三四五六七八九十\d]+局"
    match = re.search(pattern, string)
    return bool(match)


def get_video_info(video_url: str):
    # 创建Chrome浏览器选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无界面模式

    # 创建Chrome浏览器驱动
    driver = webdriver.Chrome(options=chrome_options)

    # 打开网页
    driver.get(video_url)
    # 等待网页加载完成
    time.sleep(10)

    # 获取网页标题
    title = driver.title
    if "_" in title:
        title = title.split("_")[0]
    teams, date = extract_teams_and_date(title)
    if not teams:
        logger.info(f"视频{title}不是比赛视频，URL为{video_url}")
        return None, None, None, None

    # 获取播放列表长度
    playlist_path = "#multi_page > div.cur-list > ul"
    playlist = driver.find_element(By.CSS_SELECTOR, playlist_path)
    # 遍历playlist，获取最大的数字
    playlist_idx = []
    for idx, li in enumerate(playlist.find_elements(By.TAG_NAME, "li")):
        text = li.text
        if has_match(text):
            playlist_idx.append(idx + 1)

    icon_list_selector = "#bilibili-player > div > div > div.bpx-player-primary-area > div.bpx-player-video-area > div.bpx-player-control-wrap > div.bpx-player-control-entity > div.bpx-player-control-top > div > div.bpx-player-progress-freezone"
    icon_list = driver.find_element(By.CSS_SELECTOR, icon_list_selector)
    # 查找icon_list中第一个子元素的img标签的data-seek属性
    icon_list = icon_list.find_element(By.TAG_NAME, "img")
    start_point = icon_list.get_attribute("data-seek")
    start_point = int(start_point)
    # 关闭浏览器
    driver.quit()

    return teams, date, playlist_idx, start_point


def main():
    create_logger()
    args = get_args()
    logger.debug(args)

    with open(args.video_list, "r") as f:
        video_list = json.load(f)

    with open(args.record_file, "a+") as f:
        f.seek(0)
        records = [json.loads(line) for line in f]
        f.seek(0, 2)
        for video_url in tqdm(video_list):
            if any([video_url == record["url"] for record in records]):
                logger.info(f"视频{video_url}元信息已获取")
                record = [record for record in records if record["url"] == video_url][0]
                record["start_point"] = record["start_point"] if "start_point" in record else None
                teams, date, playlist_idx, start_point = record["teams"], record["date"], record["playlist_idx"], record["start_point"]
            else:
                teams, date, playlist_idx, start_point = get_video_info(video_url)
                if teams is not None:
                    records.append(
                        {
                            "teams": teams,
                            "date": date,
                            "playlist_idx": playlist_idx,
                            "url": video_url,
                            "start_point": start_point,
                        }
                    )
                    f.write(
                        json.dumps(
                            {
                                "url": video_url,
                                "teams": teams,
                                "date": date,
                                "playlist_idx": playlist_idx,
                                "start_point": start_point,
                            }
                        )
                        + "\n"
                    )
                    f.flush()
            if teams is not None:
                logger.info(
                    f"获取到了{teams[0]} vs {teams[1]} {date} {len(playlist_idx)}P的比赛视频"
                )

                file_name = f"{teams[0]}_{teams[1]}_{date}"
                for idx, i in enumerate(playlist_idx):
                    if os.path.exists(f"{args.output_dir}/{file_name}_{idx + 1}.mp4"):
                        logger.info(f"视频{file_name}_{idx + 1}已经存在，跳过")
                        continue
                    sub_file_name = f"{file_name}_{idx + 1}"
                    logger.info(f"开始下载{sub_file_name}")
                    download(video_url + f"?p={i}", sub_file_name, args.output_dir)
                    time.sleep(15)


if __name__ == "__main__":
    main()
