import os


class Marker:
    _SYMBOL: bytes = b"C"

    @property
    def symbol(self) -> bytes:
        return self._SYMBOL

    @symbol.setter
    def symbol(self, value: bytes) -> bytes:
        if not self.is_valid_length(value):
            raise ValueError("Symbol must be a byte of length 1.")
        self._SYMBOL = value
        return self._SYMBOL

    @staticmethod
    def is_valid_length(value: bytes) -> bool:
        return len(value) == 1

    def brand(self, path: str, symbol: bytes | None = None) -> bool:
        if symbol is None:
            symbol = self._SYMBOL

        if not self.is_valid_length(symbol):
            return False

        if not os.path.exists(path):
            return False

        try:
            with open(path, "r+b") as file:
                file.seek(-1, 2)
                file.write(symbol)
                return True
        except Exception:
            return False

    def is_branded(self, path: str, symbol: bytes | None = None) -> bool:
        if symbol is None:
            symbol = self._SYMBOL

        if not self.is_valid_length(symbol):
            return False

        if not os.path.exists(path):
            return False

        try:
            with open(path, "rb") as file:
                file.seek(-1, 2)
                return file.read(1) == symbol
        except Exception:
            return False
