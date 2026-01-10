# UI(streamlit)起動
## 
```
uv run streamlit run app.py
```


# 抽出ステップ

## STEP 1 「YoutubeのURLをコピペしてmp4に変換する」

```
$ yt-dlp -x --audio-format mp4 "https://www.youtube.com/watch?v=nf357cUl8-A"
```


## STEP 2 「動画に字幕を自動生成」
- モデルは可変["tiny", "base", "small", "medium", "large"]より選べる。
- whisper-transcription直下で実行

```
$ uv run python app/localtest_script.py mp4_data/data_001.mp4 --model base
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