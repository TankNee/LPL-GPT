import argparse
import glob
import os

import pandas as pd
import whisper
from faster_whisper import WhisperModel
from loguru import logger
from tqdm import tqdm

from common import create_logger


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_dir", type=str, default="videos")
    parser.add_argument("--output_dir", type=str, default="outputs")
    parser.add_argument("--model_name", type=str, default="large")
    parser.add_argument("--model_path", type=str, default="faster-whisper-large-v2")
    return parser.parse_args()


def recognize(model: WhisperModel, video_path: str):
    df_list = []
    segments, _ = model.transcribe(
        video_path,
        beam_size=5,
        language="zh",
        repetition_penalty=1.1,
        compression_ratio_threshold=2.3,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=800),
    )
    logger.info("Transcript the video %s " % video_path)
    pbar = tqdm(segments)
    for segment in pbar:
        df_list.append([segment.start, segment.end, segment.text])
        pbar.set_postfix(
            {"End Time": f"{int(segment.end // 60)}:{int(segment.end % 60):02d}"}
        )
    df = pd.DataFrame(df_list, columns=["start", "end", "text"])
    return df


def main():
    args = get_args()
    create_logger("./logs/recognize.log")
    video_list = glob.glob(os.path.join(args.video_dir, "*.mp4"))
    model = WhisperModel(
        model_size_or_path=args.model_path, device="cuda", compute_type="float16"
    )
    # load whisper model
    for video_path in tqdm(video_list):
        segments_df = recognize(model, video_path)
        csv_path = os.path.join(
            args.output_dir, os.path.basename(video_path).replace(".mp4", ".csv")
        )
        logger.info("Save the result to %s" % csv_path)
        segments_df.to_csv(csv_path, index=False)


if __name__ == "__main__":
    main()
