"""
tools/console_utf8.py - the shared console helper for the offline tools
(RULING S5 amendment fix). Each tool's main() calls utf8_console() first:
stdout and stderr are reconfigured to UTF-8, so a player name outside the
console's code page (cp1252 on Windows) never stops a run. Every output file
is opened with encoding="utf-8" explicitly by its tool.
"""

import sys


def utf8_console():
    """Reconfigure stdout and stderr to UTF-8 where they support it (a
    StringIO under a test does not and is left alone)."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
