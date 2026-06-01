"""Generate a synthetic bug screenshot with PIL.

This draws an obviously-fake error dialog onto a canvas so the whole pipeline
can be demonstrated and tested without using any real, private screenshot.
Everything drawn here is synthetic placeholder text.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Synthetic, obviously-fake content. No real data of any kind.
_WINDOW_TITLE = "ExampleApp - Settings"
_BANNER_TEXT = "Something went wrong"
_ERROR_LINES = [
    "Unhandled exception: NullReferenceException",
    "  at ExampleApp.Settings.Save() in settings.py:142",
    "  at ExampleApp.UI.onClick(button=\"save\")",
    "  at ExampleApp.main()",
]
_HINT = "Click 'Save' on the General tab to reproduce."


def _load_font(size: int) -> ImageFont.ImageFont:
    """Load a TrueType font if available, else the PIL bitmap default."""
    for name in ("DejaVuSans.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def generate_sample(out_path: str | Path, width: int = 900, height: int = 520) -> Path:
    """Draw a synthetic error-dialog screenshot and save it to ``out_path``.

    Returns the path written. The image is a PNG regardless of suffix content;
    callers typically pass a ``.png`` path.
    """
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (width, height), color=(238, 240, 244))
    draw = ImageDraw.Draw(img)

    title_font = _load_font(22)
    body_font = _load_font(18)
    mono_font = _load_font(16)

    # Window title bar.
    draw.rectangle([0, 0, width, 44], fill=(33, 37, 43))
    draw.text((16, 11), _WINDOW_TITLE, fill=(235, 235, 235), font=title_font)

    # Red error banner.
    banner_top, banner_bottom = 70, 130
    draw.rectangle([30, banner_top, width - 30, banner_bottom], fill=(220, 53, 69))
    draw.text((50, banner_top + 16), _BANNER_TEXT, fill=(255, 255, 255), font=title_font)

    # Stack-trace panel.
    panel_top = 160
    panel_bottom = panel_top + 30 * len(_ERROR_LINES) + 20
    draw.rectangle([30, panel_top, width - 30, panel_bottom], fill=(30, 30, 30))
    y = panel_top + 14
    for line in _ERROR_LINES:
        draw.text((50, y), line, fill=(245, 120, 120), font=mono_font)
        y += 28

    # Hint line.
    draw.text((50, panel_bottom + 24), _HINT, fill=(70, 70, 70), font=body_font)

    # A fake disabled "Save" button to anchor the repro.
    btn = [width - 200, height - 70, width - 40, height - 30]
    draw.rectangle(btn, fill=(0, 123, 255))
    draw.text((btn[0] + 52, btn[1] + 9), "Save", fill=(255, 255, 255), font=body_font)

    img.save(out, format="PNG")
    return out
