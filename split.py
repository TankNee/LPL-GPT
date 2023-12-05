"""
@File    :   split.py
@Time    :   2023/11/28 13:53:22
@Author  :   TankNee
@Version :   1.0
@Desc    :   将视频按照台词和时间进行分割
"""

import argparse
import glob
import os

from loguru import logger
from moviepy.editor import VideoFileClip
from tqdm import tqdm
from Katna.video import Video
from Katna.writer import KeyFrameDiskWriter

from common import create_logger, read_json, write_json


def get_args():
    parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     "--raw_video_dir", type=str, default="raw_videos", help="原始视频文件目录"
    # )
    # parser.add_argument("--video_dir", type=str, default="videos", help="视频文件目录")
    # parser.add_argument("--subtitle_dir", type=str, default="subtitles", help="字幕文件目录")
    # parser.add_argument(
    #     "--output_dir", type=str, default="split_outputs", help="视频输出目录"
    # )
    parser.add_argument(
        "--raw_video_dir",
        type=str,
        default="/new_disk/cv_group/tanknee/Data/lpl-gpt/videos",
        help="原始视频文件目录",
    )
    parser.add_argument(
        "--video_dir",
        type=str,
        default="/new_disk/cv_group/tanknee/Data/lpl-gpt/videos-cut",
        help="视频文件目录",
    )
    parser.add_argument(
        "--subtitle_dir",
        type=str,
        default="/new_disk/cv_group/tanknee/Data/lpl-gpt/2023-spring-text/raw",
        help="字幕文件目录",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="/new_disk/cv_group/tanknee/Data/lpl-gpt/2023-spring-split",
        help="视频输出目录",
    )
    return parser.parse_args()


def cut_subtitle(subtitle: dict, cut_duration: float):
    subtitle = subtitle["body"]
    subtitle = [
        dict(
            start=item["from"] - cut_duration,
            end=item["to"] - cut_duration,
            text=item["content"],
        )
        for item in subtitle
        if item["from"] >= cut_duration
    ]
    return subtitle


def get_video_subtitle_pairs(raw_video_dir: str, video_dir: str, subtitle_dir: str):
    video_list = glob.glob(os.path.join(video_dir, "*.mp4"))
    video_subtitle_pairs = []
    for video_path in tqdm(video_list, desc="Get video subtitle pairs"):
        video_name = os.path.basename(video_path)
        # 获取视频文件的时长
        raw_video = VideoFileClip(os.path.join(raw_video_dir, video_name))
        raw_video_duration = raw_video.duration
        video = VideoFileClip(video_path)
        video_duration = video.duration
        cut_duration = raw_video_duration - video_duration
        # 获取字幕文件
        subtitle_name = video_name.replace(".mp4", ".json")
        subtitle_path = os.path.join(subtitle_dir, subtitle_name)
        if not os.path.exists(subtitle_path):
            logger.warning(f"Subtitle file {subtitle_path} does not exist")
            continue
        subtitle = read_json(subtitle_path)
        subtitle = cut_subtitle(subtitle, cut_duration)
        video_subtitle_pairs.append((video_path, subtitle))

    logger.info(f"Get {len(video_subtitle_pairs)} video subtitle pairs")
    return video_subtitle_pairs


def split_video(video_path: str, subtitle: list, output_dir: str, interval: int = 30):
    # 根据字幕和时长来拆分视频
    video = VideoFileClip(video_path)
    pre_timestamp = 0.0
    if not os.path.exists(os.path.join(output_dir, "videos")):
        os.makedirs(os.path.join(output_dir, "videos"))
        logger.info(f"Create videos directory in {os.path.join(output_dir, 'videos')}")
    if not os.path.exists(os.path.join(output_dir, "subtitles")):
        os.makedirs(os.path.join(output_dir, "subtitles"))
        logger.info(
            f"Create subtitles directory in {os.path.join(output_dir, 'subtitles')}"
        )

    video_clips = []
    pbar = tqdm(total=video.duration, desc="Split video")
    while pre_timestamp + interval < video.duration:
        timestamp = pre_timestamp
        subtitle_list = []
        for item in subtitle:
            if pre_timestamp <= item["start"] < pre_timestamp + interval:
                # 保留三位小数
                timestamp = round(min(item["end"], video.duration), 3)
                subtitle_list.append(item)
        if timestamp == pre_timestamp:
            logger.warning(
                f"Cannot find subtitle between {pre_timestamp} and {pre_timestamp + interval}"
            )
            pre_timestamp += interval
            continue
        video_clip = video.subclip(pre_timestamp, timestamp)
        video_name = os.path.basename(video_path).replace(".mp4", "")
        video_clip_path = os.path.join(
            output_dir,
            "videos",
            f"{video_name}_{pre_timestamp}_{timestamp}.mp4",
        )
        video_subtitle_path = os.path.join(
            output_dir,
            "subtitles",
            f"{video_name}_{pre_timestamp}_{timestamp}.json",
        )
        video_clip.write_videofile(video_clip_path)
        write_json(video_subtitle_path, subtitle_list)

        logger.info(
            f"Split video {video_path} from {pre_timestamp} to {timestamp} with {timestamp - pre_timestamp} seconds"
        )
        pbar.update(timestamp - pre_timestamp)
        pre_timestamp = timestamp
        video_clips.append((video_clip_path, video_subtitle_path))

    return video_clips


def extract_keyframes(video_path: str, output_dir: str, num_key_frames: int = 10):
    if not os.path.exists(os.path.join(output_dir, "keyframes")):
        os.makedirs(os.path.join(output_dir, "keyframes"))
        logger.info(
            f"Create keyframes directory in {os.path.join(output_dir, 'keyframes')}"
        )
    vd = Video()
    writer = KeyFrameDiskWriter(location=os.path.join(output_dir, "keyframes"))
    vd.extract_video_keyframes(
        no_of_frames=num_key_frames, file_path=video_path, writer=writer
    )


def main():
    create_logger("./logs/split.log")
    args = get_args()
    pairs = get_video_subtitle_pairs(
        args.raw_video_dir, args.video_dir, args.subtitle_dir
    )
    video_clips = []
    for video_path, subtitle in tqdm(pairs, desc="Split videos"):
        vc = split_video(video_path, subtitle, args.output_dir)
        video_clips.extend(vc)
    # for video_path, _ in tqdm(video_clips, desc="Extract keyframes"):
    #     extract_keyframes(video_path, args.output_dir)


if __name__ == "__main__":
    main()
