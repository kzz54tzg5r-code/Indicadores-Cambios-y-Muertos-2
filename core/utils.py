
from __future__ import annotations
import pandas as pd
import numpy as np
import unicodedata
import re


def norm_text(x) -> str:
    if x is None:
        return ""
    s = str(x).strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"\s+", " ", s)
    return s.upper()


def to_number(s):
    try:
        return pd.to_numeric(s, errors="coerce").fillna(0)
    except Exception:
        return 0


def fmt_num(v):
    try:
        return f"{float(v):,.0f}"
    except Exception:
        return "0"


def fmt_pct(v):
    try:
        return f"{float(v):,.1f}%"
    except Exception:
        return "0.0%"


def fmt_money(v):
    try:
        return f"${float(v):,.0f}"
    except Exception:
        return "$0"


def safe_div(a, b):
    try:
        return (float(a) / float(b) * 100) if float(b) else 0
    except Exception:
        return 0
