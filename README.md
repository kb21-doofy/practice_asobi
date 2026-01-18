# UI(streamlit)起動
## 
whisper-transcriptionディレクトリから実行：
```
cd whisper-transcription
uv run python -m streamlit run app/main.py
```


# 抽出ステップ

## STEP 1 「YoutubeのURLをコピペしてmp4に変換する」

```
$ yt-dlp -x --audio-format mp4 "https://www.youtube.com/watch?v=nf357cUl8-A"
```


## STEP 2 「動画に字幕を自動生成」
- whisper-transcription直下で実行

```
$ uv run python -m streamlit run app/main.py
```



# yt-dlpコマンド (YoutubeURLを入れる) 

## 基本コマンド
- URLにはダブルクォートが必要
```
$ yt-dlp "https://www.youtube.com/watch?v=nf357cUl8-A"
```

## -f オプション
- -f オプション一覧を表示（）
- -f bestvideo+bestaudio/b (最高画質でのダウンロード)
```
$ yt-dlp "https://www.youtube.com/watch?v=8bX5ASmVh4Q" -F
```

## 音声のみ（mp3）
```
$ yt-dlp -x --audio-format mp3 "https://www.youtube.com/watch?v=nf357cUl8-A"
```

## 
