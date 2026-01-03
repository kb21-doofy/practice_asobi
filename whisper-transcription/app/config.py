# 設定ファイル
import os
from typing import Optional

# TODO: 定数でリストを保持する様に集約させたい。定数の一元管理を行える様にしたい。

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
