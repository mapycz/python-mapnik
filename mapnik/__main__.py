from __future__ import print_function

import argparse
import sys
import traceback

from . import *


def mvt_preview(args):
    mvt = VectorTileMerc(0, 0, 0)
    with open(getattr(args, "in"), "rb") as f:
        merge_compressed_buffer(mvt, f.read())
    image = Image(args.size, args.size)
    if args.style:
        mapnikMap = Map(args.size, args.size)
        load_map(mapnikMap, args.style)
        preview_mvt_merc(mvt, mapnikMap, image)
    else:
        preview_mvt_merc(mvt, image)
    image.save(args.out, "png8")


def unknown_command(args):
    print("Unknown command:", args.command)
    sys.exit(1)


def main(args):
    try:
        {
            "mvt_preview": mvt_preview,
        }.get(args.command, unknown_command)(args)
    except Exception as e:
        print(traceback.format_exc())
        sys.exit(1)


if sys.argv[0].endswith("__main__.py"):
    sys.argv[0] = "python -m mapnik"

parse = argparse.ArgumentParser(
    description="Python Mapnik command line utils")
parse.add_argument("command",
                   help="commands: mvt_preview")
parse.add_argument("--style",
                   help="Path to an XML file with Mapnik style")
parse.add_argument("--size", type=int, default=256,
                   help="Size of output tile")
parse.add_argument("--in", "-i", required=True,
                   help="Input file")
parse.add_argument("--out", "-o", required=True,
                   help="Output file")

args = parse.parse_args()
main(args)
