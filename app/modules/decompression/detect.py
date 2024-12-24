from .decompress import decompressions


def detect_compression_type(p: str) -> bytes:
    with open(p, "rb") as file:
        header = file.read(10)
    for h in decompressions.keys():
        if header.startswith(h):
            return h
    return b""
