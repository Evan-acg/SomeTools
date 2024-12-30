import functools


def customer_repr(hidden: list[str] | None = None):
    if hidden is None:
        hidden = []

    def wrapper(cls):
        original__repr__ = cls.__repr__

        @functools.wraps(original__repr__)
        def __repr__(self):

            properties = [
                attr
                for attr in dir(self)
                if not attr.startswith("_") and attr not in hidden
            ]
            attrs = ", ".join(f"{attr}={getattr(self, attr)!r}" for attr in properties)
            return f"{self.__class__.__name__}({attrs})"

        cls.__repr__ = __repr__
        return cls

    return wrapper
