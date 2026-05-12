import os

# Base directory for application data (config, history, edging/paint files)
# Change APP_BASE_DIR to point to the directory where main_app.py resides
# This will place config.json, job_history.jsonl, Edging.txt, Paint.txt
# all within your project folder if you prefer that.
APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = "config.json"
JOB_HISTORY_FILE = "job_history.jsonl"

PRINTER_NAME = "ZDesigner GC420d (EPL)" # Make sure this matches your printer name

PRINTER_DPI = 203
LABEL_WIDTH_MM = 100
LABEL_HEIGHT_MM = 74
LABEL_WIDTH_DOTS = int((LABEL_WIDTH_MM / 25.4) * PRINTER_DPI)
LABEL_HEIGHT_DOTS = int((LABEL_HEIGHT_MM / 25.4) * PRINTER_DPI)

# ZPL Label Layout Constants (dots)
BOX_X_START = 30
BOX_Y_START = 20
BOX_WIDTH = 749
BOX_HEIGHT = 540
LINE_DIMENSION = 8
BORDER_THICKNESS = 4