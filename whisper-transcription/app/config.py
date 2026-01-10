# 設定ファイル
import os
from pathlib import Path
from typing import Optional


class Settings:
    """設定クラス"""
    
    def __init__(self):
        """初期化"""
        self._load_settings()
    
    def _load_settings(self) -> None:
        """
        環境変数から設定を読み込む
        
        将来的に.envファイルの読み込みやバリデーションを追加可能
        """
        self.openai_api_key = self._get_env("OPENAI_API_KEY")
        # 他の設定もここに追加可能
        
    
    @staticmethod
    def _get_env(key: str, default: Optional[str] = None) -> Optional[str]:
        """
        環境変数を取得する
        
        Args:
            key: 環境変数名
            default: デフォルト値（Noneの場合は環境変数が存在しない場合Noneを返す）
        
        Returns:
            環境変数の値、またはデフォルト値
        """
        return os.getenv(key, default)


class Constants:
    """定数クラス"""
    
    # Whisperモデル関連
    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large"]
    
    WHISPER_DEFAULT_MODEL = "base"
            
    # OpenAI LLMモデル関連
    OPENAI_AVAILABLE_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
    ]
    
    OPENAI_DEFAULT_MODEL = "gpt-4o-mini"

class SubtitleConstants:
    
    # 字幕関連の設定
    SUBTITLE_DEFAULT_FONT_SIZE = 24
    SUBTITLE_DEFAULT_FONT_COLOR = "white"
    SUBTITLE_DEFAULT_STROKE_COLOR = "black"
    SUBTITLE_DEFAULT_STROKE_WIDTH = 2
    
    # 出力ディレクトリ関連の設定
    # プロジェクトルート（whisper-transcription）を取得
    # config.pyは app/config.py にあるため、親の親ディレクトリがプロジェクトルート
    PROJECT_ROOT = Path(__file__).parent.parent.absolute()
    OUTPUT_MP4_DIR = PROJECT_ROOT / "output_mp4"