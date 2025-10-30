import requests
from urllib.parse import quote

OPSIN_BASE = "https://opsin.ch.cam.ac.uk/opsin/"

def opsin_query(name: str, out_format: str = "json", timeout: int = 10):
    """
    Query OPSIN for a given chemical name.
    out_format: 'json' (default), 'smi', 'inchi', 'png', 'svg', ...
    Returns:
      - if out_format == 'json': a dict with normalized keys (status, message, smiles, inchi, stdinchikey, cml, ...)
      - otherwise: raw response content (bytes for images, text for .smi/.inchi)
    Raises requests.HTTPError on non-200 or ValueError when OPSIN returns FAILURE status.
    """
    if not name:
        raise ValueError("Empty name provided.")
    name_enc = quote(name, safe="")   # encode all special chars
    url = f"{OPSIN_BASE}{name_enc}.{out_format}"
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()

    if out_format.lower() == "json":
        data = resp.json()
        # Normalize keys to lower-case for robustness
        data_lc = {k.lower(): v for k, v in data.items()}
        status = data_lc.get("status", "").upper()
        if status != "SUCCESS":
            # OPSIN returns JSON even for parsing failures; surface the message
            msg = data_lc.get("message") or data_lc.get("error") or "Unknown OPSIN failure"
            raise ValueError(f"OPSIN parsing failed for '{name}': {msg}")
        # return only the main useful fields (may be absent depending on name)
        return {
            "status": data_lc.get("status"),
            "message": data_lc.get("message"),
            "smiles": data_lc.get("smiles") or data_lc.get("smiles0"),
            "inchi": data_lc.get("inchi") or data_lc.get("stdinchi"),
            "stdinchikey": data_lc.get("stdinchikey"),
            "cml": data_lc.get("cml"),  # may be large
            # include the full dict if you want more
            "raw": data_lc,
        }
    else:
        # For non-json (smi, inchi, png, svg) return raw content
        # images should be written in binary mode
        return resp.content


def save_image_from_opsin(name: str, filename: str, fmt: str = "png"):
    """
    Fetch a PNG or SVG from OPSIN and save to filename.
    fmt should be 'png' or 'svg'.
    """
    if fmt.lower() not in ("png", "svg"):
        raise ValueError("format must be 'png' or 'svg'")
    content = opsin_query(name, out_format=fmt)
    with open(filename, "wb") as fh:
        fh.write(content)
    return filename


def pubchem_name_to_smiles(name):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/CanonicalSMILES/TXT"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text.strip()
    else:
        return ''
