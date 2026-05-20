#!/bin/bash
# 视频 CT PWA 图标生成脚本
# 用法：在 apps/h5/public/icons/ 下运行
#   cd apps/h5/public/icons && bash generate-icons.sh
# 依赖：需要 sips (macOS 内置) 或 ImageMagick (brew install imagemagick) 或 rsvg-convert (brew install librsvg)
#
# 如无合适工具，SVG 源文件 icon.svg 可直接用浏览器打开截图后手动裁剪

set -euo pipefail

ICON_SVG="icon.svg"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== 视频 CT PWA 图标生成 ==="
echo "源文件: $DIR/$ICON_SVG"
echo ""

# --- 方案 1: macOS sips + rsvg-convert ---
if command -v rsvg-convert &>/dev/null; then
  echo "[rsvg-convert] 检测到 rsvg-convert，使用它生成 PNG ..."

  rsvg-convert -w 192 -h 192 "$DIR/$ICON_SVG" -o "$DIR/icon-192.png"
  echo "  -> icon-192.png"

  rsvg-convert -w 512 -h 512 "$DIR/$ICON_SVG" -o "$DIR/icon-512.png"
  echo "  -> icon-512.png"

  rsvg-convert -w 512 -h 512 "$DIR/$ICON_SVG" -o "$DIR/icon-512-maskable.png"
  echo "  -> icon-512-maskable.png"

  # favicon (32x32)
  rsvg-convert -w 32 -h 32 "$DIR/$ICON_SVG" -o "$DIR/../favicon.ico"
  echo "  -> favicon.ico"

  echo ""
  echo "完成！所有图标已生成。"
  exit 0
fi

# --- 方案 2: ImageMagick ---
if command -v convert &>/dev/null; then
  echo "[ImageMagick] 检测到 convert，使用它生成 PNG ..."

  convert -background none -resize 192x192 "$DIR/$ICON_SVG" "$DIR/icon-192.png"
  echo "  -> icon-192.png"

  convert -background none -resize 512x512 "$DIR/$ICON_SVG" "$DIR/icon-512.png"
  echo "  -> icon-512.png"

  convert -background none -resize 512x512 "$DIR/$ICON_SVG" "$DIR/icon-512-maskable.png"
  echo "  -> icon-512-maskable.png"

  convert -background none -resize 32x32 "$DIR/$ICON_SVG" "$DIR/../favicon.ico"
  echo "  -> favicon.ico"

  echo ""
  echo "完成！所有图标已生成。"
  exit 0
fi

# --- 方案 3: macOS sips（需要先转成 PDF） ---
if command -v sips &>/dev/null && command -v qlmanage &>/dev/null; then
  echo "[macOS] 使用 qlmanage + sips 生成 PNG ..."

  # qlmanage 生成缩略图
  qlmanage -t -s 512 -o /tmp "$DIR/$ICON_SVG" 2>/dev/null || true
  THUMB="/tmp/icon.svg.png"

  if [ -f "$THUMB" ]; then
    sips -z 192 192 "$THUMB" --out "$DIR/icon-192.png" >/dev/null 2>&1
    echo "  -> icon-192.png"

    sips -z 512 512 "$THUMB" --out "$DIR/icon-512.png" >/dev/null 2>&1
    echo "  -> icon-512.png"

    sips -z 512 512 "$THUMB" --out "$DIR/icon-512-maskable.png" >/dev/null 2>&1
    echo "  -> icon-512-maskable.png"

    sips -z 32 32 "$THUMB" --out "$DIR/../favicon.ico" >/dev/null 2>&1
    echo "  -> favicon.ico"

    rm -f "$THUMB"
    echo ""
    echo "完成！所有图标已生成。"
    exit 0
  fi
  echo "  qlmanage 未能生成缩略图"
fi

# --- 无可用的转换工具 ---
echo "未找到 rsvg-convert / ImageMagick / qlmanage 中的任何一个。"
echo ""
echo "手动方案："
echo "  1. 用浏览器打开 $DIR/$ICON_SVG"
echo "  2. 截图后裁剪为 192x192 和 512x512"
echo "  3. 保存为 $DIR/icon-192.png 和 $DIR/icon-512.png"
echo ""
echo "或者安装任一款工具："
echo "  brew install librsvg        # rsvg-convert（推荐）"
echo "  brew install imagemagick    # convert"
exit 1
