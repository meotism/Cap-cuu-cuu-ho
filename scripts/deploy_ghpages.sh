#!/usr/bin/env bash
#
# Deploy the static site (the docs/ folder) to the gh-pages branch — WITHOUT GitHub Actions.
#
# Vì sao: GitHub Actions workflow (deploy.yml.disabled) đang tắt. Site là static thuần
# (HTML + Leaflet + GeoJSON), nội dung deploy nằm trong docs/. Script này publish docs/
# lên branch `gh-pages` ở thư mục gốc (index.html ở root) bằng git subtree — không cần
# secrets, không cần Actions, không rời branch main.
#
# Sau lần đầu: vào GitHub repo → Settings → Pages → Source = "Deploy from a branch"
#   → Branch = `gh-pages` / `(root)` → Save.
# URL: https://meotism.github.io/Cap-cuu-cuu-ho/
#
# Dùng:
#   ./scripts/deploy_ghpages.sh            # publish docs/ -> gh-pages
#   ./scripts/deploy_ghpages.sh --dry-run  # chỉ in lệnh sẽ chạy, không push
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PREFIX="docs"
BRANCH="gh-pages"
REMOTE="origin"
DRY_RUN="${1:-}"

# --- Sanity checks ---------------------------------------------------------
if [[ ! -d "$PREFIX" ]]; then
  echo "✗ Không tìm thấy thư mục '$PREFIX/'." >&2
  exit 1
fi
if [[ ! -f "$PREFIX/index.html" ]]; then
  echo "✗ '$PREFIX/index.html' không tồn tại — không có gì để deploy." >&2
  exit 1
fi
if [[ ! -f "$PREFIX/.nojekyll" ]]; then
  echo "… Tạo '$PREFIX/.nojekyll' (cần để GitHub Pages không bỏ qua file/thư mục bắt đầu bằng '_')."
  touch "$PREFIX/.nojekyll"
fi

# Cảnh báo nếu docs/ chưa được commit (subtree push chỉ publish nội dung ĐÃ commit).
if [[ -n "$(git status --porcelain -- "$PREFIX")" ]]; then
  echo "⚠  Có thay đổi chưa commit trong '$PREFIX/'. git subtree chỉ đẩy nội dung đã commit."
  echo "   Hãy commit docs/ trước:  git add $PREFIX && git commit -m 'update site'"
  if [[ "$DRY_RUN" != "--dry-run" ]]; then
    exit 1
  fi
fi

CMD="git subtree push --prefix $PREFIX $REMOTE $BRANCH"

echo "──────────────────────────────────────────────"
echo "Publish: $PREFIX/  ->  branch '$BRANCH' (root)"
echo "Lệnh:    $CMD"
echo "──────────────────────────────────────────────"

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "(dry-run) Không thực thi. Bỏ --dry-run để push thật."
  exit 0
fi

# --- Publish ---------------------------------------------------------------
eval "$CMD"

echo ""
echo "✓ Đã đẩy docs/ lên branch '$BRANCH'."
echo "  Lần đầu: Settings → Pages → Branch = $BRANCH / (root) → Save."
echo "  URL:     https://meotism.github.io/Cap-cuu-cuu-ho/"
