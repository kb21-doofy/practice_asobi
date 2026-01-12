"""
共通ロガーユーティリティ
アプリケーション全体で使用するロガーを提供
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    ロガーを取得する
    
    Args:
        name: ロガー名（通常は`__name__`を渡す）
        level: ログレベル（Noneの場合はINFOをデフォルトとして使用）
    
    Returns:
        設定済みのLoggerインスタンス
    """
    logger = logging.getLogger(name)
    
    # 既にハンドラが設定されている場合は再設定しない（重複防止）
    if logger.handlers:
        return logger
    
    # ログレベルを設定
    if level is None:
        level = logging.INFO
    logger.setLevel(level)
    
    # コンソールハンドラを作成
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    
    # フォーマッタを作成
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # ハンドラをロガーに追加
    logger.addHandler(console_handler)
    
    # 親ロガーへの伝播を防ぐ（重複ログを防ぐ）
    logger.propagate = False
    
    return logger

