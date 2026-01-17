#!/usr/bin/env python3
"""
ローカルテスト用スクリプト
main.pyの文字起こし処理を再現する


入力： mp4ファイル
出力： 字幕付きのmp4ファイル

処理の流れ：
1. mp4ファイルを読み込む
2. 仮の文字起こし結果を生成する
3. 文字起こし結果を使用してハイライトを抽出する
4. ハイライトを使用して字幕を追加する
5. 字幕付きのmp4ファイルを出力する
"""

    

import os
import sys
import argparse
import time
import tempfile
from datetime import datetime
from usecase.service.add_subtitles_service import AddSubtitlesService
from config import SubtitleConstants
from adapter.llm_factory import LLMFactory
from domain.entities.llm_provider import LLMProvider
from usecase.service.extract_highlights_service import ExtractHighlightsService
from moviepy import VideoFileClip


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="文字起こしローカルテストスクリプト")
    parser.add_argument(
        "file",
        help="文字起こしを行う音声ファイルまたは動画ファイル（mp3, wav, m4a, ogg, flac, mp4等）へのパス"
    )
    parser.add_argument(
        "--provider",
        default="openai",
        choices=["gemini", "openai"],
        help="使用するLLMプロバイダー（デフォルト: openai）"
    )
    parser.add_argument(
        "--language",
        help="音声の言語（例: ja, en）。指定しない場合は自動検出"
    )
    parser.add_argument(
        "--output",
        help="出力テキストファイルのパス。指定しない場合は標準出力"
    )
    parser.add_argument(
        "--video-output",
        help="字幕付き動画の出力パス（動画ファイルの場合のみ有効）"
    )
    
    args = parser.parse_args()

    provider_map = {
        "openai": LLMProvider.OPENAI,
        "gemini": LLMProvider.GEMINI,
    }
    selected_provider = provider_map[args.provider]
    
    # ファイルの存在確認
    if not os.path.exists(args.file):
        print(f"エラー: ファイル '{args.file}' が見つかりません。", file=sys.stderr)
        return 1
    
    # 動画ファイルの場合は音声を抽出
    temp_audio_file = None
    is_video_file = False
    original_video = None
    
    file_ext = os.path.splitext(args.file)[1].lower()
    if file_ext == ".mp4":
        is_video_file = True
        print("動画ファイルを検出しました。音声を抽出中...", file=sys.stderr)
        try:
            original_video = VideoFileClip(args.file)
            # 一時ファイルとして音声を保存
            temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_audio_file.close()
            original_video.audio.write_audiofile(temp_audio_file.name, logger=None)
            print("音声抽出完了", file=sys.stderr)
        except Exception as e:
            print(f"エラー: 動画からの音声抽出に失敗しました: {str(e)}", file=sys.stderr)
            if original_video:
                original_video.close()
            return 1
    
    # 文字起こし処理（仮）
    print("文字起こし処理中（仮）...", file=sys.stderr)
    transcribe_start = time.time()
    
    result = _build_placeholder_transcript(args.language)
    
    transcribe_end = time.time()
    
    # 処理時間計算
    transcribe_time = transcribe_end - transcribe_start
    
    print(f"処理完了（文字起こし: {transcribe_time:.2f}秒）", file=sys.stderr)
    
    # タイムスタンプ付きテキストの生成（辞書形式）
    timestamp_list = []
    for index, segment in enumerate(result["segments"]):
        start_time = segment["start"]
        end_time = segment["end"]
        text = segment["text"]
        
        # 時間をフォーマット (HH:MM:SS.ms)
        start_formatted = str(datetime.utcfromtimestamp(start_time).strftime('%H:%M:%S.%f'))[:-3]
        end_formatted = str(datetime.utcfromtimestamp(end_time).strftime('%H:%M:%S.%f'))[:-3]
        
        timestamp_list.append({
            "index": index,
            "start": start_formatted,
            "end": end_formatted,
            "text": text
        })
        
    llm_factory = LLMFactory(selected_provider)
    extract_highlights_service = ExtractHighlightsService(llm_factory)
    highlights = extract_highlights_service.extract_highlights(timestamp_list)
 
    # リストを文字列に結合（表示用）
    timestamp_text = "\n".join([
        f"[{item['start']} --> {item['end']}] {item['text']}"
        for item in timestamp_list
    ])
    
    # 結果の出力
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result["text"])
        print(f"文字起こし結果を '{args.output}' に保存しました。", file=sys.stderr)
        
        # タイムスタンプ付きテキストをファイルに保存
        timestamp_output = args.output.replace(".txt", "_timestamps.txt")
        with open(timestamp_output, "w", encoding="utf-8") as f:
            f.write(timestamp_text)
        print(f"タイムスタンプ付きテキストを '{timestamp_output}' に保存しました。", file=sys.stderr)
    else:
        print("\n" + "="*80, file=sys.stderr)
        print("文字起こし結果:", file=sys.stderr)
        print("="*80, file=sys.stderr)
        print(result["text"])
        
        print("\n" + "="*80, file=sys.stderr)
        print("タイムスタンプ付きテキスト:", file=sys.stderr)
        print("="*80, file=sys.stderr)
        print(timestamp_text)
    
    # 動画に字幕を追加（動画ファイルの場合）
    if is_video_file:
        try:
            if original_video:
                original_video.close()
            
            # 出力ディレクトリの作成（config.pyから取得）
            output_dir = SubtitleConstants.OUTPUT_MP4_DIR
            os.makedirs(output_dir, exist_ok=True)
            
            # 出力ファイル名を生成
            if args.video_output:
                video_output_path = str(output_dir / args.video_output)
            else:
                base_name = os.path.splitext(os.path.basename(args.file))[0]
                video_output_path = str(output_dir / f"{base_name}_with_subtitles.mp4")
            
            # AddSubtitlesServiceを使用して字幕を追加
            add_subtitles_service = AddSubtitlesService()
            add_subtitles_service.add_subtitles_to_video(args.file, timestamp_list, video_output_path)
        except Exception as e:
            print(f"エラー: 字幕の追加に失敗しました: {str(e)}", file=sys.stderr)
            return 1
    
    # 一時ファイルの削除
    if temp_audio_file and os.path.exists(temp_audio_file.name):
        os.unlink(temp_audio_file.name)
    
    return 0


def _build_placeholder_transcript(language: str | None) -> dict:
    text = "[placeholder] 文字起こしは未実装です。"
    if language:
        text = f"{text} language={language}"
    return {
        "text": text,
        "segments": [
            {
                "start": 0.0,
                "end": 1.0,
                "text": text,
            }
        ],
    }


if __name__ == "__main__":
    sys.exit(main())
