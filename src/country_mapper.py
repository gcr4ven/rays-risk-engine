import re
import unicodedata
from typing import Optional, Tuple

def normalize_country(raw: Optional[str]) -> str:
    if not raw:
        return ""
    s = raw.strip().lower()

    # remove accents (côte -> cote)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))

    # normalize punctuation/spaces
    s = s.replace("&", " and ")
    s = re.sub(r"[’'`]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def map_country(raw_value: Optional[str], db) -> Tuple[Optional[str], str, float, str]:
    """
    Returns: (iso2, method, confidence, raw_norm)
    method: exact | custom_override | alias | unmapped | invalid
    """
    raw_norm = normalize_country(raw_value)

    if not raw_norm:
        return None, "invalid", 0.0, raw_norm

    # 1) ISO2 direct
    if len(raw_norm) == 2 and raw_norm.isalpha():
        iso2 = raw_norm.upper()
        row = db.fetch_one(
            "select iso2 from ref_country where iso2 = %s and is_active = true",
            (iso2,)
        )
        if row:
            return iso2, "exact", 1.0, raw_norm

    # 2) Overrides
    row = db.fetch_one(
        """
        select iso2
        from country_mapping_override
        where alias_norm = %s and is_active = true
        """,
        (raw_norm,)
    )
    if row:
        return row["iso2"], "custom_override", 1.0, raw_norm

    # 3) Alias table
    row = db.fetch_one(
        """
        select iso2
        from ref_country_alias
        where alias_norm = %s
        """,
        (raw_norm,)
    )
    if row:
        return row["iso2"], "alias", 1.0, raw_norm

    return None, "unmapped", 0.0, raw_norm
