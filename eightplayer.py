import argparse
from eightplayer import gui

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="config.json", help="path to config file")
args = parser.parse_args()
gui.main(args.config)
