#!/usr/bin/env python3
"""
Whisper文字起こしコマンドラインツール
"""

import os
import sys
import time
import argparse
import whisper

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Whisper文字起こしツール")
    parser.add_argument("--file", required=True, help="文字起こしを行う音声ファイルへのパス")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"],
                        help="使用するWhisperモデルのサイズ")
    parser.add_argument("--language", help="音声の言語（例: ja, en）。指定しない場合は自動検出")
    parser.add_argument("--output", help="出力テキストファイルのパス。指定しない場合は標準出力")
    
    args = parser.parse_args()
    
    # ファイルの存在確認
    if not os.path.exists(args.file):
        print(f"エラー: ファイル '{args.file}' が見つかりません。", file=sys.stderr)
        return 1
    
    print(f"モデル '{args.model}' をロード中...", file=sys.stderr)
    start_time = time.time()
    
    # モデルのロード
    model = whisper.load_model(args.model)
    
    print(f"モデルロード完了（{time.time() - start_time:.2f}秒）", file=sys.stderr)
    print("文字起こし処理中...", file=sys.stderr)
    
    # 文字起こしオプション
    options = {}
    if args.language:
        options["language"] = args.language
    
    # 文字起こし実行
    result = model.transcribe(args.file, **options)
    
    # 結果の出力
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result["text"])
        print(f"文字起こし結果を '{args.output}' に保存しました。", file=sys.stderr)
    else:
        print("\n" + "="*80, file=sys.stderr)
        print("文字起こし結果:", file=sys.stderr)
        print("="*80, file=sys.stderr)
        print(result["text"])
    
    print(f"\n処理時間: {time.time() - start_time:.2f}秒", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())

