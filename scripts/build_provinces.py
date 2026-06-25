#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_provinces.py

Merge the authoritative Vietnamese provinces database
(thanglequoc/vietnamese-provinces-database) into the project's province data
file, ADDING ward/commune (phường/xã) data while PRESERVING the existing
lat/lng/zoom coordinates that the Leaflet map needs.

Stdlib only (json, os, shutil, sys, unicodedata).

Inputs:
  - frontend/data/vn-provinces-2025.json        (existing -> source of lat/lng/zoom/type)
  - scripts/raw/simplified_json_generated_data_vn_units_minified.json  (authoritative)

Outputs (kept in sync):
  - frontend/data/vn-provinces-2025.json
  - docs/data/vn-provinces-2025.json

Matching strategy:
  Province coordinates are matched from the OLD file by `code` first. Because the
  2025 administrative reorganization changed several province codes (and the old
  file still carried a few legacy codes), we fall back to a diacritics-insensitive
  normalized NAME match when the code is not present in the old file. If a source
  province cannot be matched to a non-null lat/lng by EITHER method, the script
  prints a clear WARNING listing those provinces and exits non-zero so missing
  coordinates never slip through silently.
"""

import json
import os
import shutil
import sys
import unicodedata

# ---------------------------------------------------------------------------
# Paths (resolved relative to the project root, i.e. the parent of scripts/)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

OLD_FILE = os.path.join(PROJECT_ROOT, "frontend", "data", "vn-provinces-2025.json")
SOURCE_FILE = os.path.join(
    SCRIPT_DIR, "raw", "simplified_json_generated_data_vn_units_minified.json"
)
OUT_FRONTEND = os.path.join(PROJECT_ROOT, "frontend", "data", "vn-provinces-2025.json")
OUT_DOCS = os.path.join(PROJECT_ROOT, "docs", "data", "vn-provinces-2025.json")

OUT_COMMENT = (
    "34 đơn vị hành chính cấp tỉnh Việt Nam (sau sáp nhập 2025) kèm danh sách "
    "phường/xã. Nguồn phường/xã: thanglequoc/vietnamese-provinces-database (MIT). "
    "Tọa độ cấp tỉnh (lat/lng/zoom) và type được giữ nguyên từ dữ liệu cũ để bản đồ "
    "Leaflet hoạt động bình thường."
)
OUT_SOURCE = (
    "https://github.com/thanglequoc/vietnamese-provinces-database "
    "(simplified_json_generated_data_vn_units_minified.json)"
)


def strip_diacritics(s):
    """Remove Vietnamese diacritics and normalize đ/Đ -> d/D for fuzzy name matching."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")


def norm_name(s):
    """Normalize a province name: lowercase, drop unit words, strip diacritics, collapse spaces."""
    s = s.lower()
    for token in ("thành phố", "tp.", "tp", "tỉnh"):
        s = s.replace(token, "")
    s = strip_diacritics(s).strip()
    return " ".join(s.split())


def derive_type(full_name):
    """Derive province type from FullName when the old file lacks it."""
    return "thành phố" if full_name.strip().lower().startswith("thành phố") else "tỉnh"


def main():
    # --- a/b. Load inputs -------------------------------------------------
    if not os.path.exists(SOURCE_FILE):
        print("ERROR: authoritative source file not found: %s" % SOURCE_FILE)
        sys.exit(1)
    if not os.path.exists(OLD_FILE):
        print("ERROR: existing province file not found: %s" % OLD_FILE)
        sys.exit(1)

    with open(OLD_FILE, "r", encoding="utf-8") as f:
        old_data = json.load(f)
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        source = json.load(f)

    old_provinces = old_data.get("provinces", [])

    # Lookup tables from the OLD file: by code and by normalized name.
    old_by_code = {p["code"]: p for p in old_provinces}
    old_by_name = {norm_name(p["name"]): p for p in old_provinces}

    # --- c. Build output provinces (deterministic: sort by source Code) ---
    source_sorted = sorted(source, key=lambda p: p["Code"])

    out_provinces = []
    missing_coords = []  # provinces with no resolvable lat/lng

    for sp in source_sorted:
        code = sp["Code"]
        name = sp["Name"]
        full_name = sp["FullName"]

        # Resolve the matching old entry: code first, then normalized name.
        old = old_by_code.get(code)
        if old is None:
            old = old_by_name.get(norm_name(name))

        lat = old.get("lat") if old else None
        lng = old.get("lng") if old else None
        zoom = old.get("zoom") if old else None

        if lat is None or lng is None:
            missing_coords.append((code, name))

        # type: prefer old file's value, else derive from FullName.
        if old and old.get("type"):
            ptype = old["type"]
        else:
            ptype = derive_type(full_name)

        wards = []
        for w in sp.get("Wards", []):
            wards.append(
                {
                    "code": w["Code"],
                    "name": w["Name"],
                    "name_en": w["NameEn"],
                    "full_name": w["FullName"],
                    "code_name": w["CodeName"],
                }
            )

        # Exact key order required by the spec.
        out_provinces.append(
            {
                "code": code,
                "name": name,
                "name_en": sp["NameEn"],
                "full_name": full_name,
                "type": ptype,
                "lat": lat,
                "lng": lng,
                "zoom": zoom,
                "wards": wards,
            }
        )

    # --- Safety net: never emit missing coordinates ----------------------
    if missing_coords:
        print("WARNING: the following source provinces have NO matching lat/lng "
              "in the existing data file (map coordinates would be null):")
        for code, name in missing_coords:
            print("  - code=%s  name=%s" % (code, name))
        print("Aborting without writing output. Add coordinates for these "
              "provinces to %s and re-run." % OLD_FILE)
        sys.exit(2)

    # --- d. Wrap result ---------------------------------------------------
    out = {
        "_comment": OUT_COMMENT,
        "_source": OUT_SOURCE,
        "provinces": out_provinces,
    }

    # --- e. Write frontend file ------------------------------------------
    with open(OUT_FRONTEND, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # --- f. Mirror to docs/data ------------------------------------------
    os.makedirs(os.path.dirname(OUT_DOCS), exist_ok=True)
    shutil.copyfile(OUT_FRONTEND, OUT_DOCS)

    # --- g. Summary -------------------------------------------------------
    total_wards = sum(len(p["wards"]) for p in out_provinces)
    size_bytes = os.path.getsize(OUT_FRONTEND)
    all_have_coords = all(
        p["lat"] is not None and p["lng"] is not None for p in out_provinces
    )

    print("Build complete.")
    print("  Provinces : %d" % len(out_provinces))
    print("  Wards     : %d" % total_wards)
    print("  Output    : %s" % OUT_FRONTEND)
    print("  Mirror    : %s" % OUT_DOCS)
    print("  File size : %d bytes (%.1f KB)" % (size_bytes, size_bytes / 1024.0))
    print("  All provinces have non-null lat/lng: %s" % ("YES" if all_have_coords else "NO"))


if __name__ == "__main__":
    main()
