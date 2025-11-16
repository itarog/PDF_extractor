
"""
text_spectra_plotter
--------------------
Parse textual descriptions of 1H NMR, 13C NMR, IR, and MS data and sketch simple spectra.

What this does
==============
- 1H NMR: creates a stick spectrum. If J values and an instrument frequency (MHz) are present,
  it will approximate simple splitting for s, d, t, q, dd (using first two J values).
- 13C NMR: creates a stick spectrum with equal intensities.
- IR: creates a stick spectrum across 4000–400 cm⁻¹. "vs/s/m/w" and "br" are parsed when present.
- MS: creates a stick spectrum (m/z vs relative intensity). If percent intensities are listed
  in parentheses, they are used; otherwise intensities are normalized equally.

Assumptions & limits
====================
- The parsers are heuristic and robust to many common writeups, but unusual formats can require
  light tweaks. Ranges like 7.50–7.42 ppm are centered; "br" is noted but not convolved as a true
  broad band. 13C multiplicities are ignored for intensity.
- For 1H NMR splitting, Hz->ppm uses the MHz parsed from the header (default 400 MHz if missing).
  Only s, d, t, q and dd are simulated with symmetric line positions.

Usage
=====
from text_spectra_plotter import (
    detect_columns, plot_spectra_from_row, parse_proton_nmr, parse_carbon_nmr, parse_ir, parse_ms
)

df = pd.read_csv("your.csv")
cols = detect_columns(df)
plot_spectra_from_row(df, row_index=0, columns_map=cols)

You can also call the individual parsers to inspect the parsed peaks.
"""

import re
import math
from typing import List, Dict, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

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

def _clip(val, lo, hi):
    return max(lo, min(hi, val))

# -------------------------------
# 1H NMR parsing and plotting
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

def _simulate_splitting(center_ppm: float, mult: Optional[str], J: List[float], freq_mhz: float) -> List[float]:
    """
    Approximate splitting positions (ppm) for simple cases based on J (Hz) and instrument MHz.
    Supported: s, d, t, q, dd (first two J values). 'm' returns the center only.
    """
    if not mult:
        return [center_ppm]

    ml = mult.lower().strip()

    def hz_to_ppm(hz: float) -> float:
        return hz / max(freq_mhz, 60.0)

    if ml.startswith("s"):
        return [center_ppm]
    if ml.startswith("m"):
        return [center_ppm]
    if ml.startswith("d") and not ml.startswith("dd"):
        # doublet: two lines +/- J/2
        J1 = J[0] if J else 7.0
        delta = hz_to_ppm(J1) / 2.0
        return [center_ppm - delta, center_ppm + delta]
    if ml.startswith("t"):
        J1 = J[0] if J else 7.0
        step = hz_to_ppm(J1)
        return [center_ppm - step, center_ppm, center_ppm + step]
    if ml.startswith("q"):
        J1 = J[0] if J else 7.0
        step = hz_to_ppm(J1)
        return [center_ppm - 1.5*step, center_ppm - 0.5*step, center_ppm + 0.5*step, center_ppm + 1.5*step]
    if ml.startswith("dd"):
        # doublet of doublets: +/- J1/2 and +/- J2/2 combinations
        if len(J) >= 2:
            d1 = hz_to_ppm(J[0]) / 2.0
            d2 = hz_to_ppm(J[1]) / 2.0
        else:
            d1 = hz_to_ppm(J[0]) / 2.0 if J else hz_to_ppm(7.0) / 2.0
            d2 = d1 * 0.7
        positions = sorted({
            center_ppm + dx + dy
            for dx in (-d1, d1) for dy in (-d2, d2)
        })
        return positions
    # fallback
    return [center_ppm]

def plot_proton_nmr(parsed: Dict, title: str = "¹H NMR", export_fname=None):
    """
    Stick plot for 1H NMR. Integration controls relative stick heights when available.
    x-axis reversed (ppm from 12 -> 0).
    """
    peaks = parsed.get("peaks", [])
    freq = parsed.get("frequency_mhz", 400.0)

    xs = []
    hs = []
    labels = []

    # Scale heights by integration if provided, else default 1
    for p in peaks:
        center = p["shift"]
        mult = p.get("mult")
        J = p.get("J", [])
        integ = p.get("int", 1.0) or 1.0
        positions = _simulate_splitting(center, mult, J, freq)
        # Equal area across components: distribute integration
        height_each = integ / max(len(positions), 1)
        for pos in positions:
            xs.append(pos)
            hs.append(height_each)
            labels.append(p.get("label", ""))

    if not xs:
        return

    # Normalize heights for display
    hs_arr = np.array(hs, dtype=float)
    if hs_arr.max() > 0:
        hs_arr = hs_arr / hs_arr.max()

    plt.figure(figsize=(10, 4))
    ax = plt.gca()

    # Sticks
    for x, h in zip(xs, hs_arr):
        ax.vlines(x, 0, h)

    ax.set_xlim(12.0, -0.2)
    ax.set_ylim(0, 1.1)
    ax.set_xlabel("δ (ppm)")
    ax.set_ylabel("Relative intensity (a.u.)")
    ax.set_title(title)

    # # Minimal annotation: annotate only the strongest ~8 sticks to avoid clutter
    # if len(xs) <= 8:
    #     annotate_n = len(xs)
    # else:
    #     idxs = np.argsort(-hs_arr)[:8]
    #     annotate_n = len(idxs)
    #     xs = [xs[i] for i in idxs]
    #     hs_arr = [hs_arr[i] for i in idxs]
    #     labels = [labels[i] for i in idxs]

    # for x, h, lab in zip(xs[:annotate_n], hs_arr[:annotate_n], labels[:annotate_n]):
    #     if lab:
    #         ax.text(x, h + 0.05, lab, rotation=90, ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    if export_fname:
        plt.savefig(export_fname)
        plt.clf()
    else:
        plt.show()
# -------------------------------
# 13C NMR parsing and plotting
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

def plot_carbon_nmr(shifts: List[float], title: str = "¹³C NMR", export_fname=None):
    """
    Stick plot for 13C NMR (equal intensities).
    """
    if not shifts:
        return

    heights = np.ones(len(shifts))
    heights = heights / heights.max()

    plt.figure(figsize=(10, 4))
    ax = plt.gca()
    for x, h in zip(shifts, heights):
        ax.vlines(x, 0, h)
    ax.set_xlim(220, -5)
    ax.set_ylim(0, 1.1)
    ax.set_xlabel("δ (ppm)")
    ax.set_ylabel("Relative intensity (a.u.)")
    ax.set_title(title)
    plt.tight_layout()
    if export_fname:
        plt.savefig(export_fname)
        plt.clf()
    else:
        plt.show()
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

def plot_ir(peaks: List[Dict], title: str = "IR (ATR/film)", export_fname=None):
    """
    Stick-like IR sketch: x reversed 4000→400 cm⁻¹, intensity up.
    """
    if not peaks:
        return

    xs = [p["wn"] for p in peaks]
    hs = [p["intensity"] for p in peaks]

    # Normalize heights
    hs = np.array(hs, dtype=float)
    if hs.max() > 0:
        hs = hs / hs.max()

    plt.figure(figsize=(10, 4))
    ax = plt.gca()
    for x, h in zip(xs, hs):
        ax.vlines(x, 0, h)
    ax.set_xlim(4000, 400)
    ax.set_ylim(0, 1.1)
    ax.set_xlabel("wavenumber (cm⁻¹)")
    ax.set_ylabel("Relative absorbance (a.u.)")
    ax.set_title(title)
    plt.tight_layout()
    if export_fname:
        plt.savefig(export_fname)
        plt.clf()
    else:
        plt.show()
# -------------------------------
# MS parsing and plotting
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

def plot_ms(peaks: List[Tuple[float, float, str]], title: str = "MS (m/z)", export_fname=None):
    """
    Stick MS plot: m/z vs relative intensity (%).
    """
    if not peaks:
        return

    xs = [p[0] for p in peaks]
    hs = [p[1] for p in peaks]

    plt.figure(figsize=(10, 4))
    ax = plt.gca()
    for x, h in zip(xs, hs):
        ax.vlines(x, 0, h)
    ax.set_xlim(0, max(xs) * 1.1 if xs else 1000)
    ax.set_ylim(0, 110)
    ax.set_xlabel("m/z")
    ax.set_ylabel("Relative intensity (%)")
    ax.set_title(title)
    plt.tight_layout()
    if export_fname:
        plt.savefig(export_fname)
        plt.clf()
    else:
        plt.show()

# -------------------------------
# CSV helpers
# -------------------------------

def _first_matching(colnames: List[str], patterns: List[str]) -> Optional[str]:
    for pat in patterns:
        rx = re.compile(pat, flags=re.I)
        for c in colnames:
            if rx.search(str(c)):
                return c
    return None

def detect_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Attempt to detect likely columns for 1H NMR, 13C NMR, IR, and MS.
    Returns a dict with keys: 'H1', 'C13', 'IR', 'MS' mapped to column names or None.
    """
    cols = [str(c) for c in df.columns]

    h1 = _first_matching(cols, [
        r"(^|\b)1\s*H\b.*NMR", r"(^|\b)H\s*NMR\b", r"\b1H\b", r"proton.*nmr",
    ])
    c13 = _first_matching(cols, [
        r"(^|\b)13\s*C\b.*NMR", r"\b13C\b", r"carbon.*nmr",
    ])
    ir = _first_matching(cols, [
        r"(^|\b)IR\b", r"infrared", r"\bFT-?IR\b"
    ])
    ms = _first_matching(cols, [
        r"(^|\b)MS\b", r"\bHRMS\b", r"mass\s*(spec|spectrum|spectrometry)"
    ])

    return {"H1": h1, "C13": c13, "IR": ir, "MS": ms}

def plot_spectra_from_row(df: pd.DataFrame, row_index: int = 0, columns_map: Optional[Dict[str, Optional[str]]] = None):
    """
    Parse and plot spectra for a given row in the DataFrame.
    Each found spectrum is plotted in its own figure.
    """
    if columns_map is None:
        columns_map = detect_columns(df)

    # 1H NMR
    h1_col = columns_map.get("H1")
    if h1_col and h1_col in df.columns and pd.notna(df.loc[row_index, h1_col]):
        h1_text = str(df.loc[row_index, h1_col])
        parsed_h1 = parse_proton_nmr(h1_text)
        title = f"¹H NMR — row {row_index}"
        plot_proton_nmr(parsed_h1, title=title)

    # 13C NMR
    c13_col = columns_map.get("C13")
    if c13_col and c13_col in df.columns and pd.notna(df.loc[row_index, c13_col]):
        c13_text = str(df.loc[row_index, c13_col])
        shifts = parse_carbon_nmr(c13_text)
        title = f"¹³C NMR — row {row_index}"
        plot_carbon_nmr(shifts, title=title)

    # IR
    ir_col = columns_map.get("IR")
    if ir_col and ir_col in df.columns and pd.notna(df.loc[row_index, ir_col]):
        ir_text = str(df.loc[row_index, ir_col])
        peaks = parse_ir(ir_text)
        title = f"IR — row {row_index}"
        plot_ir(peaks, title=title)

    # MS
    ms_col = columns_map.get("MS")
    if ms_col and ms_col in df.columns and pd.notna(df.loc[row_index, ms_col]):
        ms_text = str(df.loc[row_index, ms_col])
        peaks = parse_ms(ms_text)
        title = f"MS — row {row_index}"
        plot_ms(peaks, title=title)
