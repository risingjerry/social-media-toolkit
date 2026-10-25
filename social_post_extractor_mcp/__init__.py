"""MCP transport package for Social Media Toolkit."""

__version__ = "0.4.1"
__author__ = "risingjerry"
__email__ = "87055815+risingjerry@users.noreply.github.com"


def main():
    from .server import main as server_main

    return server_main()

__all__ = ["main"]
