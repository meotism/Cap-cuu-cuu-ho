# Task: Áp dụng vietnamese-provinces-database + vẽ ranh giới polygon + deploy gh-pages

## Mục tiêu (chốt với user)
1. Chuẩn hóa tên/mã 34 tỉnh 2025 + thêm phường/xã (nguồn: thanglequoc/vietnamese-provinces-database, MIT).
2. Khi search/bấm khu vực → **vẽ ranh giới đa giác (MULTIPOLYGON) tỉnh & phường/xã, tô màu** (giống `gis_wards.geom`). Không dùng SQLite/backend — app là static.
3. Deploy bằng **branch tĩnh gh-pages** (GitHub Actions đang tắt).

## Việc đã làm

### Data tên hành chính — `scripts/build_provinces.py`
- [x] Merge tên/mã chuẩn từ repo (`simplified_..._minified.json`) + giữ lat/lng/zoom cũ.
- [x] Match theo code, fallback theo tên không dấu (vì sáp nhập 2025 đổi vài code).
- [x] Output `frontend/data/vn-provinces-2025.json`: 34 tỉnh + 3321 xã, mỗi tỉnh có `wards[]`. Copy sang docs/.

### Ranh giới GIS — `scripts/build_boundaries.py`
- [x] Parse SQL dump Postgres GIS (WKT plaintext, không cần PostGIS) bằng shapely.
- [x] Simplify tol=0.0008 + làm tròn 5 chữ số. 0 xã unmatched, 0 geom lỗi.
- [x] Output `frontend/data/geo/provinces.json` (outline 34 tỉnh, 481KB) + `wards/<code>.json` (34 file, 1 file/tỉnh).
- [x] Tổng 7.1MB; file lớn nhất 370KB (Lâm Đồng). Copy sang docs/.
- [x] Dump nguồn 31MB để trong `scripts/raw/` + đã gitignore (tái tạo qua URL trong header script).

### UI vẽ polygon — `frontend/index.html`
- [x] Thêm dropdown phường/xã (`#wardSelect`, `#wardPanel`).
- [x] Thay marker chấm → `L.geoJSON` polygon (canvas renderer cho hiệu năng).
- [x] Chọn tỉnh → lazy-load `data/geo/wards/<code>.json`, vẽ ranh giới xã + outline tỉnh, `fitBounds`.
- [x] Chọn xã (dropdown hoặc click polygon) → tô đậm xã đó, fitBounds, tooltip full_name.
- [x] Hover highlight, loading indicator "Đang tải ranh giới…", try/catch fallback flyTo.
- [x] Clear → xóa hết layer, reset panel. Search không dấu giữ nguyên.

### Deploy gh-pages
- [x] `scripts/deploy_ghpages.sh` — `git subtree push --prefix docs origin gh-pages` (có --dry-run, kiểm tra commit).
- [x] `docs/.nojekyll`. Đường dẫn data tương đối → chạy được ở subpath `/Cap-cuu-cuu-ho/`.
- [x] README: 2 link demo + hướng dẫn bật Pages + attribution GIS + lệnh tái tạo data.

## Verify (đã chứng minh)
- [x] Data: 34 tỉnh, 3321 xã, mọi tỉnh có lat/lng, provinces.json 34 feature, tọa độ HCM/HN đúng.
- [x] JS: node --check OK, mọi symbol mới có mặt, fetch URL tương đối (no leading slash).
- [x] HTTP (python http.server): index 200, vn-provinces 200, geo/provinces 200, wards/01 (HN 126 xã) 200, wards/79 (HCM 168 xã) 200.
- [x] Sync: frontend ↔ docs giống hệt (index.html + data/), config.js cố ý khác (placeholder vs hardcoded).
- [x] Deploy script dry-run chạy đúng.

## Lưu ý quan trọng
- **Code hành chính đã đổi** theo Nghị quyết 2025: HCM = "79" (không phải "70" cũ), HN = "01", ĐN = "48", Huế = "46", Cần Thơ = "92", HP = "31".
- HCM sau sáp nhập gồm cả Bình Dương cũ (xã đầu = "Phường Thủ Dầu Một") — đúng dữ liệu.
- Khi cập nhật data: chạy lại 2 script build (tự copy docs); index.html sửa tay thì `cp` sang docs. **Đừng đè docs/config.js**.

## Chưa làm (Phase 2)
- TopoJSON toàn bộ để nhẹ hơn nữa; bật lại GitHub Actions.
- Tọa độ chính xác hơn / choropleth theo diện tích-dân số.

## Bước tiếp theo cần user
- Commit các file (geo data ~14MB, scripts, index.html, README) — chờ user đồng ý mới commit/push.
- Sau khi push gh-pages lần đầu: Settings → Pages → Branch = gh-pages / (root).
