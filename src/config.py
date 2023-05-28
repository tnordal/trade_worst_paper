"""config.py"""

import os

BASE_DIR = r"C:\Users\tnord\OneDrive\Developer\py\trade_worst_paper"

DATA_DIR = os.path.join(BASE_DIR, 'data')
STOCK_DATA = os.path.join(DATA_DIR, 'stock_data')
TICKER_FILES = os.path.join(DATA_DIR, 'ticker_files')

REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
ERROR_LOGS = os.path.join(REPORTS_DIR, 'error_logs')
OUTPUT_DIR = os.path.join(REPORTS_DIR, 'output')
