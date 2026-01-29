
"""
spectra.py
--------------------
Parse textual descriptions of 1H NMR, 13C NMR, IR, and MS data.

"""

import re
from typing import List, Dict, Tuple, Optional

import numpy as np

def parse_peaks(test_text, test_type):
    parser = None
    parsed_peaks = []
    if '1H NMR' in test_type:
        parsed_peaks = parse_proton_nmr
    elif '13C NMR' in test_type:
        parser = parse_carbon_nmr
    elif test_type == 'MS':
        parser = parse_ms
        # parsed_peaks = run_hrms_checker_full_rot(test_text)
    elif test_type =='IR':
        parser = parse_ir
    if parser:
        parsed_peaks = parser(test_text)
    return parsed_peaks



# -------------------------------
# Helpers
# -------------------------------

def _clean_text(s: str) -> str:
    return (s or "").replace("\\n", " ").replace("\n", " ").strip()

def _find_after_delta(text: str) -> str:
    s = _clean_text(text)
    if "δ" in s:
        return s.split("δ", 1)[1]
    # Sometimes a colon follows the method header
    m = re.search(r"NMR[^:]*:\s*", s, flags=re.I)
    if m:
        return s[m.end():]
    return s

def _parse_mhz(text: str, default: float = 400.0) -> float:
    m = re.search(r"(\d{2,4})\s*MHz", text, flags=re.I)
    if m:
        try:
            return float(m.group(1))
        except:
            return default
    return default

def _safe_float(x: str, default: Optional[float] = None) -> Optional[float]:
    try:
        return float(x)
    except:
        return default

def _center_of_range(a: float, b: float) -> float:
    return (a + b) / 2.0

# -------------------------------
# 1H NMR parsing
# -------------------------------

def parse_proton_nmr(text: str) -> Dict:
    """
    Parse 1H NMR textual description.
    Returns:
        {
          "frequency_mhz": float,
          "peaks": [
            {"shift": float, "range": (lo, hi) or None, "mult": str or None,
             "J": [floats in Hz], "int": float or None, "label": str}
          ]
        }
    """
    if not isinstance(text, str) or not text.strip():
        return {"frequency_mhz": 400.0, "peaks": []}

    freq = _parse_mhz(text, default=400.0)
    s = _find_after_delta(text)

    # Match sequences like: 7.26 (d, J = 8.4 Hz, 2H) or 7.52–7.40 (m, 3H)
    # Capture a number or range; optionally parentheses info that follows
    pat = re.compile(
        r"(?P<shift>\d{1,2}(?:\.\d+)?(?:\s*[–-]\s*\d{1,2}(?:\.\d+)?)?)\s*"
        r"(?:\((?P<info>[^)]*)\))?"
    )

    peaks = []
    for m in pat.finditer(s):
        shift_str = m.group("shift")
        info = (m.group("info") or "").strip()

        # Skip if this is obviously not a chemical shift (too large)
        # Accept 0–16 ppm for 1H
        # Handle ranges
        if "–" in shift_str or "-" in shift_str:
            parts = re.split(r"[–-]", shift_str)
            if len(parts) == 2:
                lo = _safe_float(parts[0].strip())
                hi = _safe_float(parts[1].strip())
                if lo is None or hi is None:
                    continue
                if not (0 <= lo <= 16 and 0 <= hi <= 16):
                    continue
                shift_val = _center_of_range(lo, hi)
                shift_range = (min(lo, hi), max(lo, hi))
            else:
                continue
        else:
            shift_val = _safe_float(shift_str)
            if shift_val is None or not (0 <= shift_val <= 16):
                continue
            shift_range = None

        info_l = info.lower()

        # multiplicity (support common cases)
        mult = None
        # Look for "br s" first
        br = re.search(r"\bbr\b", info_l)
        m_mult = re.search(
            r"\b(dd|dt|td|dq|qt|tt|s|d|t|q|quin|quint|sext|sept|hept|m)\b",
            info_l
        )
        if m_mult:
            mult = m_mult.group(1)
            if br and mult != "br":
                mult = "br " + mult

        # J values in Hz
        J = []
        for mj in re.finditer(r"J[^=\d]*=\s*([\d\.]+)", info_l):
            v = _safe_float(mj.group(1))
            if v is not None:
                J.append(v)

        # integration
        integ = None
        mi = re.search(r"(\d+(?:\.\d+)?)\s*H\b", info_l)
        if mi:
            integ = _safe_float(mi.group(1))

        # label (keep original info for annotation)
        label = info.strip()

        peaks.append({
            "shift": float(shift_val),
            "range": shift_range,
            "mult": mult,
            "J": J,
            "int": integ,
            "label": label
        })

    return {"frequency_mhz": freq, "peaks": peaks}

# -------------------------------
# 13C NMR parsing
# -------------------------------

def parse_carbon_nmr(text: str) -> List[float]:
    """
    Parse 13C NMR textual description into a list of shifts (ppm).
    """
    if not isinstance(text, str) or not text.strip():
        return []

    s = _find_after_delta(text)
    # Extract numbers 0–250 (ppm)
    vals = []
    for m in re.finditer(r"(\d{1,3}(?:\.\d+)?)", s):
        v = _safe_float(m.group(1))
        if v is not None and 0 <= v <= 250:
            vals.append(v)

    # De-duplicate near-identical shifts (e.g., 128.9 and 129.0 from rounding)
    vals = sorted(vals)
    merged = []
    for v in vals:
        if not merged or abs(v - merged[-1]) > 0.05:
            merged.append(v)
    return merged

# -------------------------------
# IR parsing and plotting
# -------------------------------

def parse_ir(text: str) -> List[Dict]:
    """
    Parse IR textual description.
    Returns a list of dicts: {"wn": float, "intensity": float, "broad": bool, "raw": str}
    Intensities mapped from tokens: vs/s/m/w/vw -> 1.0/0.8/0.55/0.3/0.2. Default 0.5.
    """
    if not isinstance(text, str) or not text.strip():
        return []

    s = _clean_text(text).lower()
    tokens = re.split(r"[;,]", s)

    def intensity_from_token(tok: str) -> float:
        m = re.search(r"(?<![a-z])vs(?![a-z])", tok)
        if m:
            return 1.0
        m = re.search(r"(?<![a-z])vw(?![a-z])", tok)
        if m:
            return 0.2
        m = re.search(r"(?<![a-z])s(?![a-z])", tok)
        if m:
            return 0.8
        m = re.search(r"(?<![a-z])m(?![a-z])", tok)
        if m:
            return 0.55
        m = re.search(r"(?<![a-z])w(?![a-z])", tok)
        if m:
            return 0.3
        return 0.5

    entries = []
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        broad = bool(re.search(r"\bbr\b|broad", tok))
        # Find all single numbers or ranges in cm^-1
        for m in re.finditer(r"(\d{3,4}(?:\.\d+)?)(?:\s*[–-]\s*(\d{3,4}(?:\.\d+)?))?", tok):
            a = _safe_float(m.group(1))
            b = _safe_float(m.group(2)) if m.group(2) else None
            if a is not None and 400 <= a <= 4000:
                inten = intensity_from_token(tok)
                if b is not None and 400 <= b <= 4000:
                    lo, hi = sorted([a, b])
                    # Represent a broad band by sampling the center
                    wn = (lo + hi) / 2.0
                    entries.append({"wn": wn, "intensity": inten, "broad": True, "raw": tok})
                else:
                    entries.append({"wn": a, "intensity": inten, "broad": broad, "raw": tok})
    return entries

# -------------------------------
# MS parsing
# -------------------------------

def parse_ms(text: str) -> List[Tuple[float, float, str]]:
    """
    Parse MS text. Returns list of (mz, rel_intensity, annotation).
    If intensities (%) are present in parentheses after an m/z, they are used.
    Otherwise, equal intensities are assigned.
    """
    if not isinstance(text, str) or not text.strip():
        return []

    s = _clean_text(text)

    # Find pairs like: 273 (100), 275 (34), ...
    pairs = []
    for m in re.finditer(r"(\d{2,5}(?:\.\d+)?)\s*\(\s*(\d{1,3})\s*\)", s):
        mz = _safe_float(m.group(1))
        inten = _safe_float(m.group(2))
        if mz is not None and 10 <= mz <= 5000 and inten is not None:
            pairs.append((mz, inten, ""))

    if not pairs:
        # If no explicit intensities, collect m/z values and set equal intensities
        mzs = []
        for m in re.finditer(r"(\d{2,5}(?:\.\d+)?)", s):
            mz = _safe_float(m.group(1))
            if mz is not None and 10 <= mz <= 5000:
                mzs.append(mz)
        mzs = sorted(set(mzs))
        pairs = [(mz, 100.0, "") for mz in mzs]

    # Normalize to base peak = 100
    intensities = np.array([p[1] for p in pairs], dtype=float)
    if intensities.max() > 0:
        intensities = 100.0 * intensities / intensities.max()

    result = []
    for (p, new_i) in zip(pairs, intensities):
        result.append((p[0], float(new_i), p[2]))

    return result
