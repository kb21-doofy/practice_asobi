# UI(streamlit)起動
## 
```
uv run streamlit run app.py
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