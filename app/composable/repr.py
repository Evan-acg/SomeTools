def customer_repr(cls):
    def __repr__(self):
        properties = [attr for attr in dir(self) if not attr.startswith("_")]
        attrs = ", ".join(f"{attr}={getattr(self, attr)!r}" for attr in properties)
        return f"{self.__class__.__name__}({attrs})"

    cls.__repr__ = __repr__
    return cls
