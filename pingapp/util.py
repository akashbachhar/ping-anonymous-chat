"""Small shared helpers for file transfer."""


def human_size(num: int) -> str:
    size = float(num)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def safe_filename(name: str) -> str:
    """Strip any directory components so a peer can't steer the write path."""
    name = name.replace("\\", "/").split("/")[-1]
    if name in ("", ".", ".."):
        return "received.bin"
    return name
