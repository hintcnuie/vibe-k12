#!/usr/bin/env python3
"""按时间点截图，用于快速自检版式（不跑整片）

  .venv/bin/python engine/snap.py out/lidong 12 30 46
"""
import os
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import find_chromium      # noqa: E402


def snap(player, times, dst_dir, w=1920, h=1080):
    os.makedirs(dst_dir, exist_ok=True)
    exe = find_chromium()
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, executable_path=exe,
                               args=["--no-sandbox", "--font-render-hinting=none",
                                     "--force-color-profile=srgb"])
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        pg.goto("file://" + os.path.abspath(player))
        pg.wait_for_function("window.__READY__ === true", timeout=15000)
        out = []
        for t in times:
            pg.evaluate("(t) => window.renderFrame(t)", float(t))
            p = os.path.join(dst_dir, f"snap_{float(t):07.2f}.png")
            pg.screenshot(path=p, animations="disabled")
            out.append(p)
        b.close()
    return out


if __name__ == "__main__":
    d = sys.argv[1]
    times = [float(x) for x in sys.argv[2:]]
    for p in snap(os.path.join(d, "player.html"), times, os.path.join(d, "snaps")):
        print(p)
