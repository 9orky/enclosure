__all__ = ["__version__"]

try:
    from . import _version

    __version__ = _version.version
except ImportError:
    __version__ = "0.0.0.dev0"
