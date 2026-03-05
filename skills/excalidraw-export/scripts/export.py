#!/usr/bin/env python3
"""Export .excalidraw files to SVG/PNG.

Pipeline: .excalidraw JSON -> kroki.io (SVG) -> Chrome headless (PNG)

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
        # kroki returns error images as PNG with error message
        if body[:4] == b"\x89PNG":
            print(json.dumps({"status": "error", "error": f"kroki.io returned error image (HTTP {e.code})", "hint": "The excalidraw JSON might be malformed", "recoverable": False}), file=sys.stderr)
        else:
            print(json.dumps({"status": "error", "error": f"kroki.io HTTP {e.code}: {body[:200].decode(errors='replace')}", "hint": "Check the excalidraw JSON format", "recoverable": False}), file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(json.dumps({"status": "error", "error": f"Cannot reach kroki.io: {e.reason}", "hint": "Check your internet connection", "recoverable": True}), file=sys.stderr)
        sys.exit(1)


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


def _svg_to_png_chrome(svg_data: bytes, output_path: str, scale: int, chrome: str) -> bool:
    """Render SVG to PNG via Chrome headless. Returns True on success."""
    import re
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

    # Chrome needs extra viewport padding (viewport < window-size)
    win_w, win_h = svg_w + 40, svg_h + 100

    try:
        result = subprocess.run(
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
            # Auto-crop: the PNG may have extra white space from the viewport padding.
            # Use Python to trim it if Pillow is available, otherwise leave as-is.
            try:
                from PIL import Image, ImageChops

                img = Image.open(output_path)
                bg = Image.new(img.mode, img.size, (255, 255, 255))
                diff = ImageChops.difference(img, bg)
                bbox = diff.getbbox()
                if bbox:
                    # Add small padding
                    pad = 4
                    crop = (
                        max(0, bbox[0] - pad),
                        max(0, bbox[1] - pad),
                        min(img.width, bbox[2] + pad),
                        min(img.height, bbox[3] + pad),
                    )
                    img.crop(crop).save(output_path)
            except ImportError:
                pass  # No Pillow, skip auto-crop
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    finally:
        os.unlink(tmp_html)
    return False


def svg_to_png(svg_data: bytes, output_path: str, scale: int = 2) -> None:
    """Convert SVG bytes to PNG using available backend.

    Priority: Chrome headless > resvg > rsvg-convert > cairosvg
    Chrome renders embedded woff2 fonts perfectly (hand-drawn Excalifont + CJK).
    """
    import subprocess
    import shutil
    import tempfile

    # Try Chrome headless first (perfect font rendering with embedded woff2)
    chrome = _find_chrome()
    if chrome:
        if _svg_to_png_chrome(svg_data, output_path, scale, chrome):
            return

    # Try resvg (good quality, uses system fonts for CJK fallback)
    if shutil.which("resvg"):
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            tmp.write(svg_data)
            tmp_svg = tmp.name
        try:
            subprocess.run(
                ["resvg", "--zoom", str(scale), tmp_svg, output_path],
                check=True,
                capture_output=True,
            )
            return
        finally:
            os.unlink(tmp_svg)

    # Try rsvg-convert (brew install librsvg)
    if shutil.which("rsvg-convert"):
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            tmp.write(svg_data)
            tmp_svg = tmp.name
        try:
            dpi = 96 * scale
            subprocess.run(
                ["rsvg-convert", "-d", str(dpi), "-p", str(dpi), "-o", output_path, tmp_svg],
                check=True,
                capture_output=True,
            )
            return
        finally:
            os.unlink(tmp_svg)

    # Try cairosvg — may have issues with embedded woff2 fonts
    try:
        import cairosvg

        cairosvg.svg2png(bytestring=svg_data, write_to=output_path, scale=scale)
        return
    except ImportError:
        pass

    print(json.dumps({"status": "error", "error": "No SVG-to-PNG backend found", "hint": "Install Google Chrome (recommended) or: brew install resvg / brew install librsvg / pip install cairosvg", "recoverable": False}), file=sys.stderr)
    sys.exit(2)


def preflight() -> None:
    """Check dependencies and print JSON status."""
    import shutil

    deps = {}

    # Python
    deps["python3"] = {"status": "ok", "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"}

    # SVG-to-PNG backends
    chrome = _find_chrome()
    if chrome:
        deps["chrome"] = {"status": "ok", "path": chrome}
    else:
        deps["chrome"] = {"status": "missing", "hint": "Install Google Chrome for perfect woff2 font rendering"}

    for tool in ["resvg", "rsvg-convert"]:
        path = shutil.which(tool)
        deps[tool] = {"status": "ok", "path": path} if path else {"status": "missing"}

    try:
        import cairosvg  # noqa: F401
        deps["cairosvg"] = {"status": "ok"}
    except ImportError:
        deps["cairosvg"] = {"status": "missing"}

    has_png_backend = any(deps[k]["status"] == "ok" for k in ["chrome", "resvg", "rsvg-convert", "cairosvg"])

    # kroki.io connectivity
    try:
        req = urllib.request.Request("https://kroki.io/", headers={"User-Agent": "excalidraw-export-skill/1.0"})
        urllib.request.urlopen(req, timeout=5)
        deps["kroki.io"] = {"status": "ok"}
    except Exception as e:
        deps["kroki.io"] = {"status": "error", "hint": f"Cannot reach kroki.io: {e}"}

    ready = deps["kroki.io"]["status"] == "ok" and has_png_backend
    result = {
        "status": "ok" if ready else "error",
        "dependencies": deps,
        "hint": "All dependencies ready" if ready else "Missing required dependencies",
    }
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
