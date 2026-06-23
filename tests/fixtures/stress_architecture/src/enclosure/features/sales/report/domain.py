import os, sys  # noqa: E401,F401
from .application import run as app_run


class Alpha:
    def first(self, value, extra=0):
        return value + extra

    def second(self):
        return 2


class Beta:
    pass


def first(value):
    return value


def second():
    return app_run("demo")
