#!/usr/bin/env python3
"""
抽象的な文字起こしサービス
"""

import os
from typing import Optional, Dict, Any, List
from config import Constants


class TranscriptionService:
    """抽象的な文字起こしサービスクラス"""

    def __init__(self, model_name: str = "standard", device: Optional[str] = None):
        """
        初期化

        Args:
            model_name: 使用する処理モード名（デフォルト: "standard"）
            device: 使用するデバイス。Noneの場合は"cpu"固定
        """
        if model_name not in Constants.AVAILABLE_MODELS:
            raise ValueError(f"無効なモード名: {model_name}。利用可能: {Constants.AVAILABLE_MODELS}")

        self.model_name = model_name
        self.device = device if device else "cpu"
        self._initialized = False

    def load_model(self) -> str:
        """
        文字起こし処理の初期化（抽象的な処理）

        Returns:
            初期化されたモード名
        """
        if not self._initialized:
            self._initialized = True
        return self.model_name

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        音声ファイルを文字起こしする（抽象的な処理）

        Args:
            audio_path: 音声ファイルのパス
            language: 言語コード（例: "ja", "en"）。Noneの場合は未指定
            **kwargs: 将来的な拡張用

        Returns:
            文字起こし結果の辞書（text, segments等を含む）
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"ファイルが見つかりません: {audio_path}")

        _ = kwargs
        self.load_model()

        placeholder_text = (
            f"[{self.model_name}] 文字起こしは未実装です。"
            f" language={language or 'auto'}"
        )
        segments = self._build_placeholder_segments(placeholder_text)

        return {
            "language": language or "auto",
            "text": placeholder_text,
            "segments": segments,
        }

    def get_device(self) -> str:
        """
        現在使用しているデバイスを取得

        Returns:
            デバイス名
        """
        return self.device

    @staticmethod
    def check_ffmpeg() -> bool:
        """
        FFmpegがインストールされているか確認

        Returns:
            FFmpegがインストールされている場合True
        """
        return os.system("ffmpeg -version > /dev/null 2>&1") == 0

    @staticmethod
    def get_available_models() -> List[str]:
        """
        利用可能な処理モードの一覧を取得

        Returns:
            モード名のリスト
        """
        return Constants.AVAILABLE_MODELS.copy()

    @staticmethod
    def _build_placeholder_segments(text: str) -> List[Dict[str, Any]]:
        """抽象的なセグメントを作成"""
        return [
            {
                "id": 0,
                "start": 0.0,
                "end": 1.0,
                "text": text,
            }
        ]
