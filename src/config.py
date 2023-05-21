# config.py

import os

# from pathlib import Path  # pathlib is seriously awesome!
# data_dir = Path('/path/to/some/logical/parent/dir')
# data_path = data_dir / 'my_file.csv'  # use feather files if possible!!!


BASE_DIR = r"C:\Users\tnord\OneDrive\Developer\py\trade_worst_paper"

DATA_DIR = os.path.join(BASE_DIR, 'data')
STOCK_DATA = os.path.join(DATA_DIR, 'stock_data')
TICKER_FILES = os.path.join(DATA_DIR, 'ticker_files')

REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
ERROR_LOGS = os.path.join(REPORTS_DIR, 'error_logs')
OUTPUT_DIR = os.path.join(REPORTS_DIR, 'output')
