#!/usr/bin/env python3
"""
Whisper文字起こしサービス
"""

import os
import whisper
import torch
from typing import Optional, Dict, Any, List
from config import Constants


class WhisperService:
    """Whisper文字起こしサービスクラス"""
    
    def __init__(self, model_name: str = "base", device: Optional[str] = None):
        """
        初期化
        
        Args:
            model_name: 使用するWhisperモデル名（デフォルト: "base"）
            device: 使用するデバイス（"cuda" or "cpu"）。Noneの場合は自動検出
        """
        if model_name not in Constants.AVAILABLE_MODELS:
            raise ValueError(f"無効なモデル名: {model_name}。利用可能: {Constants.AVAILABLE_MODELS}")
        
        self.model_name = model_name
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self._model = None
    
    def load_model(self) -> whisper.Whisper:
        """
        Whisperモデルをロードする
        
        Returns:
            ロードされたWhisperモデル
        """
        if self._model is None:
            self._model = whisper.load_model(self.model_name, device=self.device)
        return self._model
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        音声ファイルを文字起こしする
        
        Args:
            audio_path: 音声ファイルのパス
            language: 言語コード（例: "ja", "en"）。Noneの場合は自動検出
            **kwargs: whisper.transcribe()に渡す追加オプション
        
        Returns:
            文字起こし結果の辞書（text, segments等を含む）
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"ファイルが見つかりません: {audio_path}")
        
        model = self.load_model()
        
        options = {}
        if language:
            options["language"] = language
        options.update(kwargs)
        
        result = model.transcribe(audio_path, **options)
        return result
    
    def get_device(self) -> str:
        """
        現在使用しているデバイスを取得
        
        Returns:
            デバイス名（"cuda" or "cpu"）
        """
        return self.device
    
    @staticmethod
    def is_gpu_available() -> bool:
        """
        GPUが利用可能かどうかを確認
        
        Returns:
            GPUが利用可能な場合True
        """
        return torch.cuda.is_available()
    
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
        利用可能なWhisperモデルの一覧を取得
        
        Returns:
            モデル名のリスト
        """
        return Constants.AVAILABLE_MODELS.copy()

