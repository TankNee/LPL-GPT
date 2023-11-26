import argparse
import glob
import os
from loguru import logger
import whisper
from whisper import Whisper

from common import create_logger


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_dir", type=str, default="videos")
    parser.add_argument("--output_dir", type=str, default="output")
    parser.add_argument("--model_name", type=str, default="base")
    parser.add_argument("--model_path", type=str, default="path/to/model")
    return parser.parse_args()
    
def recognize(model: Whisper, video_path: str):
    result = model.transcribe(video_path)
    return result["text"]

def main():
    args = get_args()
    create_logger()

    video_list = glob.glob(os.path.join(args.video_dir, "*.mp4"))
    # load whisper model
    model = whisper.load_model(name=args.model_name, download_root=args.model_path)
    for video_path in video_list:
        res = recognize(model, video_path)
        logger.info(f"{video_path}: {res}")

if __name__ == "__main__":
    main()