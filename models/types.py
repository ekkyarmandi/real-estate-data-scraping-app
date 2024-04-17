from datetime import datetime as dt


class Base:

    def set(self, value):
        try:
            return self.func(value)
        except TypeError:
            return None


class Text(Base):

    def func(self, value):
        value = str(value)
        if value.strip() == "" or value == "None":
            return None
        else:
            return value


class Boolean(Base):

    def __init__(self):
        self.func = bool


class Integer(Base):

    def func(self, value):
        value = int(value)
        if value == 0:
            return None
        else:
            return value


class Float(Base):

    def func(self, value):
        value = float(value)
        if value == 0.0:
            return None
        else:
            return value


class DateTime(Base):

    def func(self, value):
        try:
            return dt.strptime(value, r"%Y-%m-%d %H:%M:%S")
        except ValueError:
            return dt.strptime(value, r"%Y-%m-%d")
