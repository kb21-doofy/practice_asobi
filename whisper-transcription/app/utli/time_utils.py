"""
時間関連のユーティリティ関数
"""


def time_to_seconds(time_str: str | int | float) -> float:
    """
    時間文字列（HH:MM:SS.ms）を秒数に変換
    
    Args:
        time_str: 時間文字列（例: "00:02:19.000"）または秒数（float/int）
    
    Returns:
        秒数（float）
    """
    if isinstance(time_str, (int, float)):
        return float(time_str)

    parts = time_str.strip().split(":")
    if len(parts) == 2:
        hours = 0
        minutes = int(parts[0])
        seconds_token = parts[1]
    elif len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_token = parts[2]
    else:
        raise ValueError(f"Unsupported time format: {time_str}")

    seconds_parts = seconds_token.split(".")
    seconds = int(seconds_parts[0])
    milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
    
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
    return total_seconds
