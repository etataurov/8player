#! /usr/bin/env python3
import argparse
import logging
from eightplayer import gui

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="config.json", help="path to config file")
parser.add_argument("--debug", action="store_true", help="set debug log level")
parser.add_argument("--inspector", action="store_true", help="show webkit inspector")
args = parser.parse_args()
loglevel = logging.DEBUG if args.debug else logging.INFO
logging.basicConfig(level=loglevel)
gui.main(args.config, args.inspector)
