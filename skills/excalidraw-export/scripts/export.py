#!/usr/bin/env python3
"""Export .excalidraw files to SVG/PNG.

Pipeline: .excalidraw JSON -> kroki.io (SVG) -> text-to-path + resvg (PNG)

The SVG from kroki.io embeds hand-drawn fonts (Excalifont + Xiaolai) as woff2
in @font-face rules. Since resvg cannot parse @font-face, we extract the
embedded woff2 glyphs via fonttools and convert SVG <text> to <path> elements.
This preserves the hand-drawn style without needing a browser engine.

Usage:
    python export.py input.excalidraw                     # -> input.png
    python export.py input.excalidraw -o output.png       # -> output.png
    python export.py input.excalidraw -f svg              # -> input.svg
    python export.py input.excalidraw -f svg -f png       # -> both
    python export.py input.excalidraw --scale 3           # -> 3x resolution
    python export.py input.excalidraw --dark              # -> dark theme
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

KROKI_URL = "https://kroki.io/excalidraw/svg"


def excalidraw_to_svg(input_path: str, dark: bool = False) -> bytes:
    """Convert .excalidraw JSON to SVG via kroki.io."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = f.read()

    # Validate JSON
    try:
        scene = json.loads(data)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "error": f"Invalid JSON in {input_path}: {e}", "hint": "Check the .excalidraw file syntax", "recoverable": False}), file=sys.stderr)
        sys.exit(2)

    # Apply dark theme if requested
    if dark:
        if "appState" not in scene:
            scene["appState"] = {}
        scene["appState"]["exportWithDarkMode"] = True
        scene["appState"]["viewBackgroundColor"] = "#1e1e1e"
        data = json.dumps(scene)

    req = urllib.request.Request(
        KROKI_URL,
        data=data.encode("utf-8"),
        headers={
            "Content-Type": "text/plain",
            "User-Agent": "excalidraw-export-skill/1.0",
            "Accept": "image/svg+xml",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        body = e.read()
        if body[:4] == b"\x89PNG":
            print(json.dumps({"status": "error", "error": f"kroki.io returned error image (HTTP {e.code})", "hint": "The excalidraw JSON might be malformed", "recoverable": False}), file=sys.stderr)
        else:
            print(json.dumps({"status": "error", "error": f"kroki.io HTTP {e.code}: {body[:200].decode(errors='replace')}", "hint": "Check the excalidraw JSON format", "recoverable": False}), file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(json.dumps({"status": "error", "error": f"Cannot reach kroki.io: {e.reason}", "hint": "Check your internet connection", "recoverable": True}), file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Text-to-path conversion: extract woff2 glyphs, replace <text> with <path>
# ---------------------------------------------------------------------------

def _extract_fonts(svg_text: str) -> dict:
    """Extract embedded woff2 fonts from SVG @font-face rules.

    Returns dict mapping @font-face family name -> [TTFont, ...].
    """
    import base64
    import tempfile
    from fontTools.ttLib import TTFont

    font_faces = re.findall(r"@font-face\s*\{[^}]+\}", svg_text)
    fonts = {}

    for ff in font_faces:
        family_m = re.search(r"font-family:\s*([^;]+)", ff)
        data_m = re.search(r"url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)", ff)
        if not family_m or not data_m:
            continue

        family = family_m.group(1).strip().strip("\"'")
        woff2_bytes = base64.b64decode(data_m.group(1))

        tmp = tempfile.NamedTemporaryFile(suffix=".woff2", delete=False)
        tmp.write(woff2_bytes)
        tmp.close()

        try:
            font = TTFont(tmp.name)
        finally:
            os.unlink(tmp.name)

        if family not in fonts:
            fonts[family] = []
        fonts[family].append(font)

    return fonts


def _glyph_path(font, char):
    """Get SVG path data and advance width for a character."""
    from fontTools.pens.svgPathPen import SVGPathPen

    cmap = font.getBestCmap()
    if not cmap or ord(char) not in cmap:
        return None
    glyph_name = cmap[ord(char)]
    glyph_set = font.getGlyphSet()
    if glyph_name not in glyph_set:
        return None
    glyph = glyph_set[glyph_name]
    pen = SVGPathPen(glyph_set)
    glyph.draw(pen)
    return pen.getCommands(), glyph.width


def _text_to_paths(content, fonts_by_family, font_families_str,
                   font_size_px, text_x, text_y, text_anchor, fill):
    """Convert a text string to SVG <path> elements.

    Coordinates match SVG text rendering with dominant-baseline="alphabetic":
    - text_x, text_y are relative to the parent <g> transform
    - text_y is the alphabetic baseline
    - text_anchor controls horizontal alignment
    """
    families = [f.strip().strip("\"'") for f in font_families_str.split(",")]
    available_fonts = []
    for fam in families:
        if fam in fonts_by_family:
            available_fonts.extend(fonts_by_family[fam])
    if not available_fonts:
        return None

    first_font = available_fonts[0]
    upm = first_font["head"].unitsPerEm
    ascender = first_font["hhea"].ascent
    scale = font_size_px / upm

    # Measure total width and collect glyph paths
    cursor = 0  # in font units
    glyphs = []
    for char in content:
        if char == " ":
            cursor += upm * 0.25
            continue
        found = False
        for font in available_fonts:
            result = _glyph_path(font, char)
            if result:
                path_data, glyph_width = result
                if path_data:
                    glyphs.append((cursor * scale, path_data))
                cursor += glyph_width
                found = True
                break
        if not found:
            cursor += upm * 0.5

    total_width = cursor * scale

    # text-anchor offset
    if text_anchor == "middle":
        anchor_offset = -total_width / 2
    elif text_anchor == "end":
        anchor_offset = -total_width
    else:
        anchor_offset = 0

    # Build <path> elements.
    # Font glyphs: y-up with origin at baseline.
    # SVG: y-down. Flip with scale(s, -s) at the baseline position.
    paths = []
    for glyph_x_px, path_data in glyphs:
        tx = text_x + anchor_offset + glyph_x_px
        ty = text_y
        transform = f"translate({tx:.3f},{ty:.3f}) scale({scale:.6f},-{scale:.6f})"
        paths.append(f'<path d="{path_data}" fill="{fill}" transform="{transform}"/>')

    return "\n".join(paths) if paths else None


def svg_text_to_paths(svg_data: bytes) -> bytes:
    """Replace <text> elements in SVG with <path> using embedded font glyphs.

    This preserves hand-drawn fonts (Excalifont, Xiaolai) without needing
    a browser engine. The <g> wrappers with translate/rotate transforms are
    kept intact; only the <text> inside is replaced with <path> elements.

    Returns modified SVG bytes, or original if conversion is not possible.
    """
    try:
        from fontTools.ttLib import TTFont  # noqa: F401
    except ImportError:
        return svg_data  # fonttools not available, return original

    svg_text = svg_data.decode("utf-8")

    # Check if there are any @font-face rules to process
    if "@font-face" not in svg_text:
        return svg_data

    fonts = _extract_fonts(svg_text)
    if not fonts:
        return svg_data

    text_re = re.compile(r'<text\s+([^>]*)>(.*?)</text>', re.DOTALL)

    def replace_text(match):
        attrs_str = match.group(1)
        content = match.group(2)

        def get_attr(name, default=""):
            m = re.search(rf'{name}="([^"]*)"', attrs_str)
            return m.group(1) if m else default

        x = float(get_attr("x", "0"))
        y = float(get_attr("y", "0"))
        font_family = get_attr("font-family", "Excalifont")
        font_size = float(get_attr("font-size", "20px").replace("px", ""))
        fill = get_attr("fill", "#1e1e1e")
        text_anchor = get_attr("text-anchor", "start")

        result = _text_to_paths(
            content, fonts, font_family, font_size,
            x, y, text_anchor, fill
        )
        return result if result else match.group(0)

    converted = text_re.sub(replace_text, svg_text)

    # Remove @font-face style blocks (paths don't need them)
    converted = re.sub(
        r"<defs>\s*<style[^>]*>.*?</style>\s*</defs>",
        "", converted, flags=re.DOTALL,
    )

    # Clean up font objects
    for font_list in fonts.values():
        for font in font_list:
            font.close()

    return converted.encode("utf-8")


# ---------------------------------------------------------------------------
# PNG backends
# ---------------------------------------------------------------------------

def _find_chrome() -> str | None:
    """Find Chrome/Chromium binary on the system."""
    import shutil

    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "/Applications/Chromium.app/Contents/MacOS/Chromium",  # macOS Chromium
        "google-chrome",  # Linux
        "google-chrome-stable",  # Linux
        "chromium-browser",  # Linux
        "chromium",  # Linux
    ]
    for c in candidates:
        if os.path.isfile(c) or shutil.which(c):
            return c
    return None


def _svg_to_png_resvg(svg_data: bytes, output_path: str, scale: int) -> bool:
    """Render SVG to PNG via resvg. Returns True on success."""
    import shutil
    import subprocess
    import tempfile

    if not shutil.which("resvg"):
        return False

    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        tmp.write(svg_data)
        tmp_svg = tmp.name

    try:
        result = subprocess.run(
            ["resvg", "--zoom", str(scale), tmp_svg, output_path],
            capture_output=True,
            timeout=30,
        )
        return result.returncode == 0 and os.path.isfile(output_path) and os.path.getsize(output_path) > 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
    finally:
        os.unlink(tmp_svg)


def _svg_to_png_chrome(svg_data: bytes, output_path: str, scale: int, chrome: str) -> bool:
    """Render SVG to PNG via Chrome headless. Returns True on success."""
    import subprocess
    import tempfile

    # Extract SVG viewBox dimensions
    svg_text = svg_data[:2000].decode("utf-8", errors="replace")
    m = re.search(r'viewBox="([^"]+)"', svg_text)
    if not m:
        return False
    parts = m.group(1).split()
    svg_w, svg_h = int(float(parts[2]) + 1), int(float(parts[3]) + 1)

    # Wrap SVG in minimal HTML for precise sizing
    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<style>*{{margin:0;padding:0;overflow:hidden}}'
        f'body{{width:{svg_w}px;height:{svg_h}px;background:#fff}}</style>'
        f'</head><body>{svg_data.decode("utf-8")}</body></html>'
    )

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write(html)
        tmp_html = tmp.name

    win_w, win_h = svg_w + 40, svg_h + 100

    try:
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--force-device-scale-factor={scale}",
                f"--screenshot={output_path}",
                f"--window-size={win_w},{win_h}",
                f"file://{tmp_html}",
            ],
            capture_output=True,
            timeout=15,
        )
        if os.path.isfile(output_path) and os.path.getsize(output_path) > 0:
            # Auto-crop viewport padding if Pillow is available
            try:
                from PIL import Image, ImageChops

                img = Image.open(output_path)
                bg = Image.new(img.mode, img.size, (255, 255, 255))
                diff = ImageChops.difference(img, bg)
                bbox = diff.getbbox()
                if bbox:
                    pad = 4
                    crop = (
                        max(0, bbox[0] - pad),
                        max(0, bbox[1] - pad),
                        min(img.width, bbox[2] + pad),
                        min(img.height, bbox[3] + pad),
                    )
                    img.crop(crop).save(output_path)
            except ImportError:
                pass
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    finally:
        os.unlink(tmp_html)
    return False


def svg_to_png(svg_data: bytes, output_path: str, scale: int = 2) -> None:
    """Convert SVG bytes to PNG.

    Priority:
    1. text-to-path + resvg (fast, no browser, preserves hand-drawn fonts)
    2. Chrome headless (fallback, perfect but heavy)
    3. resvg without text-to-path (loses hand-drawn fonts)
    """
    import shutil

    # 1. Try text-to-path + resvg (recommended)
    if shutil.which("resvg"):
        pathed_svg = svg_text_to_paths(svg_data)
        if _svg_to_png_resvg(pathed_svg, output_path, scale):
            return

    # 2. Fallback: Chrome headless with original SVG (has @font-face)
    chrome = _find_chrome()
    if chrome:
        if _svg_to_png_chrome(svg_data, output_path, scale, chrome):
            return

    # 3. Fallback: resvg without text-to-path (system fonts)
    if shutil.which("resvg"):
        if _svg_to_png_resvg(svg_data, output_path, scale):
            return

    print(json.dumps({
        "status": "error",
        "error": "No PNG backend available",
        "hint": "Install resvg (brew install resvg) + fonttools (pip install fonttools brotli), or Google Chrome",
        "recoverable": False,
    }), file=sys.stderr)
    sys.exit(2)


def preflight() -> None:
    """Check dependencies and print JSON status."""
    import shutil

    deps = {}

    # Python
    deps["python3"] = {
        "status": "ok",
        "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }

    # fonttools + brotli (for text-to-path)
    try:
        import fontTools  # noqa: F401
        from fontTools.pens.svgPathPen import SVGPathPen  # noqa: F401
        deps["fonttools"] = {"status": "ok"}
    except ImportError:
        deps["fonttools"] = {"status": "missing", "hint": "pip install fonttools brotli"}

    try:
        import brotli  # noqa: F401
        deps["brotli"] = {"status": "ok"}
    except ImportError:
        deps["brotli"] = {"status": "missing", "hint": "pip install brotli (needed for woff2 decompression)"}

    # resvg
    resvg_path = shutil.which("resvg")
    deps["resvg"] = {"status": "ok", "path": resvg_path} if resvg_path else {
        "status": "missing", "hint": "brew install resvg",
    }

    # Chrome (optional fallback)
    chrome = _find_chrome()
    deps["chrome"] = {"status": "ok", "path": chrome} if chrome else {
        "status": "optional", "hint": "Optional fallback: Google Chrome",
    }

    # Best path: resvg + fonttools + brotli
    has_text_to_path = all(
        deps[k]["status"] == "ok" for k in ["resvg", "fonttools", "brotli"]
    )
    has_any_backend = has_text_to_path or (chrome is not None) or (resvg_path is not None)

    # kroki.io connectivity
    try:
        req = urllib.request.Request("https://kroki.io/", headers={"User-Agent": "excalidraw-export-skill/1.0"})
        urllib.request.urlopen(req, timeout=5)
        deps["kroki.io"] = {"status": "ok"}
    except Exception as e:
        deps["kroki.io"] = {"status": "error", "hint": f"Cannot reach kroki.io: {e}"}

    ready = deps["kroki.io"]["status"] == "ok" and has_any_backend
    hint = "All dependencies ready"
    if ready and has_text_to_path:
        hint = "All dependencies ready (text-to-path + resvg, no Chrome needed)"
    elif ready and not has_text_to_path:
        hint = "Working, but install fonttools+brotli for best results without Chrome"
    elif not ready:
        hint = "Missing required dependencies"

    result = {"status": "ok" if ready else "error", "dependencies": deps, "hint": hint}
    print(json.dumps(result))
    sys.exit(0 if ready else 1)


def main():
    parser = argparse.ArgumentParser(
        description="Export .excalidraw files to SVG/PNG"
    )
    parser.add_argument("input", nargs="?", help="Input .excalidraw file")
    parser.add_argument("--preflight", action="store_true", help="Check dependencies and exit")
    parser.add_argument("-o", "--output", help="Output file path (auto-detected from format)")
    parser.add_argument(
        "-f",
        "--format",
        action="append",
        choices=["png", "svg"],
        help="Output format(s). Can specify multiple. Default: png",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=2,
        help="PNG scale factor (default: 2 for retina)",
    )
    parser.add_argument(
        "--dark",
        action="store_true",
        help="Export with dark theme",
    )
    args = parser.parse_args()

    if args.preflight:
        preflight()

    if not args.input:
        parser.error("the following arguments are required: input")

    if not os.path.isfile(args.input):
        print(json.dumps({"status": "error", "error": f"File not found: {args.input}", "hint": "Check the file path", "recoverable": False}), file=sys.stderr)
        sys.exit(2)

    formats = args.format or ["png"]
    base = os.path.splitext(args.input)[0]

    # Get SVG from kroki
    svg_data = excalidraw_to_svg(args.input, dark=args.dark)

    results = []

    if "svg" in formats:
        svg_path = args.output if (args.output and len(formats) == 1) else f"{base}.svg"
        with open(svg_path, "wb") as f:
            f.write(svg_data)
        results.append(svg_path)

    if "png" in formats:
        png_path = args.output if (args.output and "svg" not in formats) else f"{base}.png"
        svg_to_png(svg_data, png_path, scale=args.scale)
        results.append(png_path)

    output = {
        "status": "ok",
        "files": [{"path": os.path.abspath(r), "size": os.path.getsize(r)} for r in results],
        "hint": f"Exported {len(results)} file(s)",
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
