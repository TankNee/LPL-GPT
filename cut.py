import argparse
import os
import subprocess
import time

from loguru import logger

from common import read_jsonl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record_files", type=str, default="./config/records.jsonl")
    parser.add_argument("--video_dir", type=str, default="videos")
    parser.add_argument("--output_dir", type=str, default="cut_videos")
    args = parser.parse_args()
    return args

def get_start_point(video_url):
    # 创建Chrome浏览器选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无界面模式

    # 创建Chrome浏览器驱动
    driver = webdriver.Chrome(options=chrome_options)

    # 打开网页
    driver.get(video_url)
    # 等待网页加载完成
    time.sleep(15)

    # 获取播放列表长度
    icon_list_selector = "#bilibili-player > div > div > div.bpx-player-primary-area > div.bpx-player-video-area > div.bpx-player-control-wrap > div.bpx-player-control-entity > div.bpx-player-control-top > div > div.bpx-player-progress-freezone"
    icon_list = driver.find_element(By.CSS_SELECTOR, icon_list_selector)
    # 查找icon_list中第一个子元素的img标签的data-seek属性
    icon_list = icon_list.find_element(By.TAG_NAME, "img")
    start_point = icon_list.get_attribute("data-seek")
    start_point = int(start_point)

    # 关闭浏览器
    driver.quit()

    return start_point

def cut_video(input_file, output_file, start_time):
    # 使用ffmpeg命令行工具剪切视频
    subprocess.run(['ffmpeg', '-ss', start_time, '-i', input_file, '-c', 'copy', output_file])


def main():
    args = get_args()
    records = read_jsonl(args.record_files)
    records = [record for record in records if record["playlist_idx"]]
    for record in records:
        video_url = record["url"]
        offset = 0 if record["playlist_idx"][0] == 1 else 1
        for idx in record["playlist_idx"]:
            teams = record["teams"]
            date = record["date"]
            teams = "_".join(teams)
            input_file = os.path.join(args.video_dir, f"{teams}_{date}_{idx + offset}.mp4")
            output_file = os.path.join(args.output_dir, f"{teams}_{date}_{idx + offset}.mp4")
            if os.path.exists(output_file):
                logger.info(f"{output_file} 已存在")
                continue

            start_point = get_start_point(video_url + f"?p={idx + offset}")
            logger.info(f"{teams}_{date}_{idx + offset} 的开始时间为{start_point}")

            if start_point == 0 or not os.path.exists(input_file):
                logger.warning(f"{teams}_{date}_{idx + offset} 的开始时间为{start_point}，该文件不存在，跳过")
                continue

            cut_video(input_file, output_file, str(start_point))
            time.sleep(30)


if __name__ == "__main__":
    main()