"""
@File    :   split.py
@Time    :   2023/11/28 13:53:22
@Author  :   TankNee
@Version :   1.0
@Desc    :   将视频按照台词和时间进行分割
"""

import argparse
import glob
from multiprocessing import Pool
import os
import sys

from loguru import logger
from moviepy.editor import VideoFileClip
from tqdm import tqdm
from Katna.video import Video
from Katna.writer import KeyFrameDiskWriter

from common import create_logger

args = {
    "split_video_dir": "/new_disk/cv_group/tanknee/Data/lpl-gpt/2023-spring-split/videos",
    "output_dir": "/new_disk/cv_group/tanknee/Data/lpl-gpt/2023-spring-split",
    # "split_video_dir": "/disk0/cv_group/tanknee/CodeRepo/LPL-GPT/outputs/videos",
    # "output_dir": "/disk0/cv_group/tanknee/CodeRepo/LPL-GPT/outputs",
    "num_key_frames": 15,
}


args = argparse.Namespace(**args)

def extract_keyframes(video_path: str):
    if not os.path.exists(os.path.join(args.output_dir, "keyframes")):
        os.makedirs(os.path.join(args.output_dir, "keyframes"))
        logger.info(
            f"Create keyframes directory in {os.path.join(args.output_dir, 'keyframes')}"
        )
    video_name = ".".join(os.path.basename(video_path).split(".")[:-1])
    if os.path.exists(os.path.join(args.output_dir, "keyframes", f"{video_name}_0.jpeg")):
        return
    vd = Video(parallel=False, ordered=True)
    writer = KeyFrameDiskWriter(location=os.path.join(args.output_dir, "keyframes"))
    vd.extract_video_keyframes(
        no_of_frames=args.num_key_frames, file_path=video_path, writer=writer
    )


def main():
    create_logger("./logs/extract.log")
    videos = glob.glob(os.path.join(args.split_video_dir, "*.mp4"))

    logger.info(f"Extracting keyframes from {len(videos)} videos")
    start_point = 0.7
    end_point = 1.0
    for i, video in enumerate(tqdm(videos)):
        if i <= start_point * len(videos):
            continue
        if i >= end_point * len(videos):
            break
        extract_keyframes(video)


if __name__ == "__main__":
    main()
