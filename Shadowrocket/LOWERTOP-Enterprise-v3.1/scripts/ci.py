#!/usr/bin/env python3
from pathlib import Path
import traceback

import build

try:
    build.main()
except Exception:
    root = Path(__file__).resolve().parents[1]
    out = root / 'build'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'build-error.txt').write_text(traceback.format_exc(), encoding='utf-8')
    raise
