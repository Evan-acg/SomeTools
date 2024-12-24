import threading
import typing as t


def singleton(cls: type) -> t.Any:
    instance: dict[type, t.Any] = {}
    lock: threading.Lock = threading.Lock()

    def get_instance(*args: t.Any, **kwargs: t.Any) -> t.Any:
        with lock:
            if cls not in instance:
                instance[cls] = cls(*args, **kwargs)
        return instance[cls]

    return get_instance


class SingletonMeta(type):
    _instance: dict[type, t.Any] = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args: t.Any, **kwargs: t.Any) -> t.Any:
        with cls._lock:
            if cls not in cls._instance:
                instance: t.Any = super().__call__(*args, **kwargs)
                cls._instance[cls] = instance
        return cls._instance[cls]
