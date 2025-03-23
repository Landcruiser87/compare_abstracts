from __future__ import annotations

import argparse
import logging
import platform
import sys
from support import logger

if sys.version_info < (3, 8):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

from __init__ import JSONTreeApp, __prog_name__, __version__

WINDOWS = platform.system() == "Windows"
DEBUGPY_PORT = 5678


def main():
    parser = argparse.ArgumentParser(
        prog=__prog_name__, description="Json Tree Andy", epilog=f"v{__version__}"
    )
    parser.add_argument(
        "-V",
        "--version",
        help="Show version information.",
        action="version",
        version=f"%(prog)s {__version__} (Textual v{importlib_metadata.version( 'textual' )})",
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=argparse.FileType(encoding="utf-8", mode="r"),
        metavar="PATH",
        help="path to file, or stdin",
        default=sys.stdin,
    )
    
    parser.add_argument(
        "--log", nargs="?", help="Log level for enable debugpy", default="INFO"
    )

    args = parser.parse_args()
    numeric_level = getattr(logging, args.log.upper(), None)

    if not isinstance(numeric_level, int):
        logger.warning(f"Invalid log level {args.log!r}")

    # if numeric_level == logging.DEBUG:
    #     import debugpy
    #     debugpy.listen(DEBUGPY_PORT)
    #     debugpy.wait_for_client()

    try:
        # See:Textualize/textual/issues/153#issuecomment-1256933121
        if not WINDOWS:
            sys.stdin = open("/dev/tty", "r")

        app = JSONTreeApp(args.path)
        app.run()

        if not sys.stdin.closed:
            sys.stdin.close()

    except Exception as error:
        logger.warning(f"Unable to read {args.path!r}; {error}")
        sys.exit(-1)

if __name__ == "__main__":
    main()



#TODO .  Fork JTREE /adapt TUI for different json tree exploration.
    #various categories that are found within that years scrape.  Might need to
    #update each keyword for sites to get better category data for sorting

#Sidebar expands out from left side and allows you to regroup by the following categories.  
    #dataset ID
    #institution - Will need to go with either first person or majority of institution among authors
    #timezone - lol 
    #topic cosine sim
    #abstract cosine sim
        #cosine sim to current selected abstract above... eh 80 percent.  
        #(or put an input box to control that)
    #abstract summary text wrap.
