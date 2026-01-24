# 抽出ステップ

## STEP 1 「YoutubeのURLをコピペしてmp4に変換する」
```
$ yt-dlp -f "bv*+ba/b" --merge-output-format mp4 "https://www.youtube.com/watch?v=Jxf1L4fVrB4"
```

## STEP 2 「動画に字幕を自動生成」
- whisper-transcription直下で実行
```
$ uv run python -m streamlit run app/main.py
```
