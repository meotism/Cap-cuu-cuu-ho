#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_boundaries.py

Offline pipeline that converts the Vietnamese province + ward boundary geometry
from the thanglequoc/vietnamese-provinces-database GIS dataset into simplified,
per-province GeoJSON files that a static Leaflet site can lazy-load.

----------------------------------------------------------------------------
Data source / how to regenerate
----------------------------------------------------------------------------
The PostgreSQL GIS SQL dump (WKT plaintext, ~145MB unzipped) comes from:
  https://raw.githubusercontent.com/thanglequoc/vietnamese-provinces-database/master/postgresql/gis/postgresql_ImportData_gis_2026-06-20__12_32_01.sql.zip

For reproducibility, the (31MB) source zip is committed at scripts/raw/gis.sql.zip.
The 145MB unzipped .sql is NOT committed; it lives in the scratchpad temp dir.

To regenerate the GeoJSON output:
  1. pip install shapely
  2. python3 scripts/build_boundaries.py
The script locates the unzipped .sql in the scratchpad, falling back to unzipping
scripts/raw/gis.sql.zip (or the scratchpad zip) if the .sql is missing.

The dump contains two relevant INSERT blocks, one statement per line:
  INSERT INTO gis_provinces(province_code, gis_server_id, area_km2, bbox, geom) VALUES ('52',...,ST_GeomFromText('POLYGON((bbox))',4326),ST_GeomFromText('MULTIPOLYGON(((...)))',4326));
  INSERT INTO gis_wards(ward_code, gis_server_id, area_km2, bbox, geom) VALUES ('03907',...,ST_GeomFromText('POLYGON((bbox))',4326),ST_GeomFromText('MULTIPOLYGON(((...)))',4326));
Columns: code, gis_server_id, area_km2, bbox (a POLYGON), geom (the real MULTIPOLYGON).
The LAST ST_GeomFromText per row is the geom we want. Coordinates are "lng lat"
(SRID 4326), matching GeoJSON [lng, lat].

----------------------------------------------------------------------------
Outputs (mirrored to docs/ for Vercel)
----------------------------------------------------------------------------
  frontend/data/geo/provinces.json            FeatureCollection of 34 provinces
  frontend/data/geo/wards/<province_code>.json FeatureCollection of that province's wards
  docs/data/geo/**                            byte-identical mirror
"""

import json
import os
import re
import shutil
import sys
import zipfile

try:
    from shapely import wkt as shapely_wkt
    from shapely.geometry import mapping
except ImportError:
    sys.stderr.write(
        "ERROR: shapely is required. Install it with:  pip install shapely\n"
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

SCRATCHPAD = (
    "/private/tmp/claude-501/-Users-trantuan-Documents-Cap-cuu-cuu-ho/"
    "d90cb8bb-10a6-46aa-bdc6-3549577282d8/scratchpad"
)
SQL_BASENAME = "postgresql_ImportData_gis_2026-06-20__12_32_01.sql"
ZIP_BASENAME = "gis.sql.zip"
DOWNLOAD_URL = (
    "https://raw.githubusercontent.com/thanglequoc/vietnamese-provinces-database/"
    "master/postgresql/gis/postgresql_ImportData_gis_2026-06-20__12_32_01.sql.zip"
)

NAMES_FILE = os.path.join(PROJECT_ROOT, "frontend", "data", "vn-provinces-2025.json")
RAW_DIR = os.path.join(SCRIPT_DIR, "raw")
FRONTEND_GEO = os.path.join(PROJECT_ROOT, "frontend", "data", "geo")
DOCS_GEO = os.path.join(PROJECT_ROOT, "docs", "data", "geo")

# Simplification tolerance (degrees). 0.0008 ~ 90m. Bumped to keep per-province
# ward files comfortably small while still resembling real boundaries.
SIMPLIFY_TOLERANCE = 0.0008
COORD_DECIMALS = 5
SIZE_WARN_BYTES = 600 * 1024

# Single-quotes never appear inside the WKT payload, so this is safe even though
# WKT itself contains commas and parens.
GEOM_RE = re.compile(r"ST_GeomFromText\('([^']*)'\s*,\s*4326\)")
# Leading code of a row. Two row shapes exist in this dump:
#   gis_provinces: one full statement per line -> "... VALUES ('CODE',..."
#   gis_wards:     a "INSERT ... VALUES" header line followed by bare data rows
#                  each starting with "('CODE',...".
# This matches the code in either shape (optionally preceded by VALUES).
CODE_RE = re.compile(r"(?:VALUES\s*)?\(\s*'([^']*)'")
# area_km2: the number right before the FIRST ST_GeomFromText.
AREA_RE = re.compile(r",\s*([0-9]+(?:\.[0-9]+)?)\s*,\s*ST_GeomFromText")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def locate_sql():
    """Find the unzipped .sql dump, unzipping a source zip if necessary."""
    candidates = [os.path.join(SCRATCHPAD, SQL_BASENAME)]
    for c in candidates:
        if os.path.exists(c):
            return c

    # Need to unzip. Prefer the scratchpad zip, then the committed raw zip.
    zip_candidates = [
        os.path.join(SCRATCHPAD, ZIP_BASENAME),
        os.path.join(RAW_DIR, ZIP_BASENAME),
    ]
    for z in zip_candidates:
        if os.path.exists(z):
            print("Unzipping %s -> %s" % (z, SCRATCHPAD))
            os.makedirs(SCRATCHPAD, exist_ok=True)
            with zipfile.ZipFile(z) as zf:
                zf.extractall(SCRATCHPAD)
            target = os.path.join(SCRATCHPAD, SQL_BASENAME)
            if os.path.exists(target):
                return target
            # The archive may use a different inner name; find the first .sql.
            for name in zf.namelist():
                if name.endswith(".sql"):
                    return os.path.join(SCRATCHPAD, name)

    sys.stderr.write(
        "ERROR: could not locate the GIS .sql dump or a zip to unzip.\n"
        "Download it from:\n  %s\n"
        "and place it (or the unzipped .sql) in:\n  %s\n" % (DOWNLOAD_URL, SCRATCHPAD)
    )
    sys.exit(1)


def save_raw_zip():
    """Copy the 31MB source zip into scripts/raw/ for reproducibility."""
    os.makedirs(RAW_DIR, exist_ok=True)
    dst = os.path.join(RAW_DIR, ZIP_BASENAME)
    if os.path.exists(dst):
        return dst
    src = os.path.join(SCRATCHPAD, ZIP_BASENAME)
    if os.path.exists(src):
        shutil.copyfile(src, dst)
        print("Saved source zip -> %s" % dst)
        return dst
    print("WARNING: source zip not found at %s; skipping raw/ copy." % src)
    return None


def round_coords(obj):
    """Recursively round every numeric coordinate in a GeoJSON geometry dict."""
    if isinstance(obj, float):
        return round(obj, COORD_DECIMALS)
    if isinstance(obj, list):
        return [round_coords(x) for x in obj]
    if isinstance(obj, tuple):
        return [round_coords(x) for x in obj]
    if isinstance(obj, dict):
        return {k: round_coords(v) for k, v in obj.items()}
    return obj


def parse_block(text, is_row, label):
    """
    Parse every data row in the dump for which is_row(line) is True.

    In this dump the two blocks have DIFFERENT physical shapes and are
    interleaved throughout the file, so we classify each line individually
    rather than splitting on header positions:
      - gis_provinces: one complete "INSERT INTO gis_provinces ... VALUES (...)"
        statement per line.
      - gis_wards: a bare "INSERT INTO gis_wards(...) VALUES" header line followed
        by data rows that each start with "('CODE',...)".

    A valid row is any matched line that actually contains ST_GeomFromText
    (this naturally skips the bare gis_wards header lines, which end at VALUES).

    Returns {code: {"area_km2": float|None, "geom": <shapely geom>}}.
    Drops empty/invalid geometries with a warning.
    """
    result = {}
    skipped_empty = 0
    for line in text.splitlines():
        if not is_row(line):
            continue
        if "ST_GeomFromText" not in line:
            # e.g. the bare "INSERT INTO gis_wards(...) VALUES" header line.
            continue

        code_m = CODE_RE.search(line)
        if not code_m:
            continue
        code = code_m.group(1)

        geom_matches = GEOM_RE.findall(line)
        if not geom_matches:
            print("  WARNING [%s] no ST_GeomFromText for code=%s; skipping." % (label, code))
            continue
        # The LAST match is the real geom MULTIPOLYGON (the first is the bbox).
        geom_wkt = geom_matches[-1]

        area_m = AREA_RE.search(line)
        area_km2 = float(area_m.group(1)) if area_m else None

        try:
            geom = shapely_wkt.loads(geom_wkt)
        except Exception as exc:  # noqa: BLE001
            print("  WARNING [%s] failed to parse WKT for code=%s: %s" % (label, code, exc))
            continue

        if geom.is_empty:
            print("  WARNING [%s] empty geometry for code=%s; skipping." % (label, code))
            skipped_empty += 1
            continue

        geom = geom.simplify(SIMPLIFY_TOLERANCE, preserve_topology=True)

        if geom.is_empty:
            print("  WARNING [%s] geometry became empty after simplify for code=%s; skipping." % (label, code))
            skipped_empty += 1
            continue
        if not geom.is_valid:
            # Try to repair; if still invalid we keep it (Leaflet is forgiving)
            # but warn so it's visible.
            fixed = geom.buffer(0)
            if not fixed.is_empty and fixed.is_valid:
                geom = fixed
            else:
                print("  WARNING [%s] invalid geometry for code=%s (kept as-is)." % (label, code))

        result[code] = {"area_km2": area_km2, "geom": geom}

    if skipped_empty:
        print("  [%s] skipped %d empty geometries." % (label, skipped_empty))
    return result


def geom_to_geojson(geom):
    """Convert a shapely geometry to a rounded GeoJSON geometry dict."""
    return round_coords(mapping(geom))


def dir_size_bytes(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return total


def human_kb(n):
    return "%.1f KB" % (n / 1024.0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("== build_boundaries.py ==")
    print("Simplify tolerance: %s, coord decimals: %d" % (SIMPLIFY_TOLERANCE, COORD_DECIMALS))

    # 1. Locate dump + save reproducible source zip.
    sql_path = locate_sql()
    print("Using SQL dump: %s (%.1f MB)" % (sql_path, os.path.getsize(sql_path) / 1e6))
    save_raw_zip()

    with open(sql_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    # 2. Parse both blocks. Classify each line by shape (see parse_block docstring).
    #    Province rows are self-contained INSERT statements; ward data rows are
    #    bare tuples beginning with "('".
    def is_province_row(line):
        return "INSERT INTO gis_provinces" in line

    def is_ward_row(line):
        # Bare ward data row, or a (rare) single-line gis_wards INSERT.
        return line.startswith("('") or "INSERT INTO gis_wards" in line

    print("Parsing gis_provinces ...")
    provinces_geom = parse_block(text, is_province_row, "provinces")
    print("  parsed %d province geometries." % len(provinces_geom))

    print("Parsing gis_wards ...")
    wards_geom = parse_block(text, is_ward_row, "wards")
    print("  parsed %d ward geometries." % len(wards_geom))

    # 3. Build name lookups + ward_code -> province_code from the names file.
    with open(NAMES_FILE, "r", encoding="utf-8") as f:
        names_data = json.load(f)

    province_name = {}       # code -> name (display)
    province_full = {}       # code -> full_name
    ward_name = {}           # code -> name
    ward_full = {}           # code -> full_name
    ward_to_province = {}    # ward_code -> province_code

    for p in names_data.get("provinces", []):
        pcode = p["code"]
        province_name[pcode] = p.get("name")
        province_full[pcode] = p.get("full_name")
        for w in p.get("wards", []):
            wcode = w["code"]
            ward_name[wcode] = w.get("name")
            ward_full[wcode] = w.get("full_name")
            ward_to_province[wcode] = pcode

    # 4. Write provinces.json (FeatureCollection of all provinces).
    os.makedirs(FRONTEND_GEO, exist_ok=True)
    wards_dir = os.path.join(FRONTEND_GEO, "wards")
    # Start clean so stale files never linger.
    if os.path.isdir(wards_dir):
        shutil.rmtree(wards_dir)
    os.makedirs(wards_dir, exist_ok=True)

    province_features = []
    for code in sorted(provinces_geom.keys()):
        geom = provinces_geom[code]["geom"]
        province_features.append(
            {
                "type": "Feature",
                "properties": {
                    "code": code,
                    "name": province_name.get(code, code),
                },
                "geometry": geom_to_geojson(geom),
            }
        )

    provinces_fc = {"type": "FeatureCollection", "features": province_features}
    provinces_path = os.path.join(FRONTEND_GEO, "provinces.json")
    with open(provinces_path, "w", encoding="utf-8") as f:
        json.dump(provinces_fc, f, ensure_ascii=False, separators=(",", ":"))
    print("Wrote %s (%d features)." % (provinces_path, len(province_features)))

    # 5. Group wards by province and write one file per province.
    unmatched = []           # GIS ward codes not present in the names file
    grouped = {}             # province_code -> [ward feature, ...]
    for wcode in sorted(wards_geom.keys()):
        pcode = ward_to_province.get(wcode)
        if pcode is None:
            unmatched.append(wcode)
            continue
        feature = {
            "type": "Feature",
            "properties": {
                "code": wcode,
                "name": ward_name.get(wcode),
                "full_name": ward_full.get(wcode),
                "area_km2": wards_geom[wcode]["area_km2"],
            },
            "geometry": geom_to_geojson(wards_geom[wcode]["geom"]),
        }
        grouped.setdefault(pcode, []).append(feature)

    ward_file_sizes = []     # (province_code, path, bytes)
    total_ward_features = 0
    for pcode in sorted(grouped.keys()):
        features = grouped[pcode]
        total_ward_features += len(features)
        fc = {"type": "FeatureCollection", "features": features}
        path = os.path.join(wards_dir, "%s.json" % pcode)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(fc, f, ensure_ascii=False, separators=(",", ":"))
        ward_file_sizes.append((pcode, path, os.path.getsize(path)))

    # 6. Mirror the whole geo tree to docs/data/geo.
    if os.path.isdir(DOCS_GEO):
        shutil.rmtree(DOCS_GEO)
    os.makedirs(os.path.dirname(DOCS_GEO), exist_ok=True)
    shutil.copytree(FRONTEND_GEO, DOCS_GEO)
    print("Mirrored geo tree -> %s" % DOCS_GEO)

    # 7. Summary.
    geo_bytes = dir_size_bytes(FRONTEND_GEO)
    ward_file_sizes.sort(key=lambda t: t[2], reverse=True)
    top3 = ward_file_sizes[:3]

    print("\n================ SUMMARY ================")
    print("Simplify tolerance used : %s" % SIMPLIFY_TOLERANCE)
    print("Provinces written       : %d" % len(province_features))
    print("Ward files written      : %d" % len(ward_file_sizes))
    print("Total ward features     : %d" % total_ward_features)
    print("Unmatched GIS wards     : %d (skipped)" % len(unmatched))
    if unmatched:
        print("  unmatched codes (first 20): %s" % ", ".join(unmatched[:20]))
    print("Total frontend/data/geo : %d bytes (%s)" % (geo_bytes, human_kb(geo_bytes)))
    print("3 largest ward files:")
    for pcode, path, size in top3:
        nm = province_name.get(pcode, pcode)
        print("  %s (%s): %s" % (os.path.basename(path), nm, human_kb(size)))

    over = [t for t in ward_file_sizes if t[2] > SIZE_WARN_BYTES]
    if over:
        print("\nWARNING: %d per-province ward file(s) exceed %d KB:" % (len(over), SIZE_WARN_BYTES // 1024))
        for pcode, path, size in over:
            print("  %s (%s): %s" % (os.path.basename(path), province_name.get(pcode, pcode), human_kb(size)))
        print("Consider increasing SIMPLIFY_TOLERANCE (e.g. 0.0012) and rerunning.")
    else:
        print("\nAll per-province ward files are under %d KB." % (SIZE_WARN_BYTES // 1024))
    print("========================================")


if __name__ == "__main__":
    main()
