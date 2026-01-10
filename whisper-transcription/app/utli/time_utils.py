"""
時間関連のユーティリティ関数
"""


def time_to_seconds(time_str: str) -> float:
    """
    時間文字列（HH:MM:SS.ms）を秒数に変換
    
    Args:
        time_str: 時間文字列（例: "00:02:19.000"）
    
    Returns:
        秒数（float）
    """
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds_parts = parts[2].split(".")
    seconds = int(seconds_parts[0])
    milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
    
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
    return total_seconds

