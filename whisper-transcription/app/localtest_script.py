#!/usr/bin/env python3
"""
ローカルテスト用スクリプト
main.pyのwhisper_service処理を再現する
"""

import os
import sys
import argparse
import time
from datetime import datetime
from usecase.service.whisper_service import WhisperService
from config import Constants


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Whisper文字起こしローカルテストスクリプト")
    parser.add_argument(
        "file",
        help="文字起こしを行う音声ファイルへのパス"
    )
    parser.add_argument(
        "--model",
        default="base",
        choices=Constants.AVAILABLE_MODELS,
        help=f"使用するWhisperモデルのサイズ（デフォルト: base）"
    )
    parser.add_argument(
        "--language",
        help="音声の言語（例: ja, en）。指定しない場合は自動検出"
    )
    parser.add_argument(
        "--output",
        help="出力テキストファイルのパス。指定しない場合は標準出力"
    )
    
    args = parser.parse_args()
    
    # ファイルの存在確認
    if not os.path.exists(args.file):
        print(f"エラー: ファイル '{args.file}' が見つかりません。", file=sys.stderr)
        return 1
    
    # サービスの初期化
    print(f"モデル '{args.model}' をロード中...", file=sys.stderr)
    load_start = time.time()
    
    whisper_service = WhisperService(model_name=args.model)
    whisper_service.load_model()  # モデルをロード
    
    load_end = time.time()
    print(f"モデルロード完了（{load_end - load_start:.2f}秒）", file=sys.stderr)
    
    # 文字起こし処理
    print("文字起こし処理中...", file=sys.stderr)
    transcribe_start = time.time()
    
    # 文字起こし実行（main.pyと同じ処理）
    result = whisper_service.transcribe(
        args.file,
        language=args.language if args.language else None
    )
    
    transcribe_end = time.time()
    
    # 処理時間計算
    transcribe_time = transcribe_end - transcribe_start
    total_time = transcribe_end - load_start
    
    print(f"処理完了（文字起こし: {transcribe_time:.2f}秒、合計: {total_time:.2f}秒）", file=sys.stderr)
    
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
    
    #TODO timestamp_listをプロンプトに投げて、highlightを抽出する
    print("99999", timestamp_list)
    
    
    
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
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
