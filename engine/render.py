#!/usr/bin/env python3
"""逐帧渲染：Playwright 驱动无头 Chromium，按时间码截图"""
import glob
import os

from playwright.sync_api import sync_playwright


def find_chromium():
    """优先用已有的 Chromium，避免重复下载几百 MB。
    也可用环境变量 VK12_CHROMIUM 指定路径。"""
    env = os.environ.get("VK12_CHROMIUM")
    if env and os.path.exists(env):
        return env
    base = os.path.expanduser("~/Library/Caches/ms-playwright")
    for pat in ("/chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium",
                "/chromium_headless_shell-*/chrome-headless-shell-mac-*/chrome-headless-shell"):
        found = sorted(glob.glob(base + pat))
        if found:
            return found[-1]
    return None


def render_frames(player_path, frames_dir, total, fps, width, height,
                  clip=None, log=print, high_perf=True, fmt="png", quality=95):
    """high_perf=True 时主动请求独显（macOS 双显卡机型上 --force_high_performance_gpu
    会把 ANGLE Metal 从 Intel 核显切到 AMD 独显，实测约快 15~20%）。"""
    os.makedirs(frames_dir, exist_ok=True)
    dur = clip if clip else total
    n = max(1, int(round(dur * fps)))

    exe = find_chromium()
    args = ["--no-sandbox", "--disable-dev-shm-usage",
            "--font-render-hinting=none", "--force-color-profile=srgb"]
    if high_perf:
        args.append("--force_high_performance_gpu")

    ext = "jpg" if fmt == "jpg" else "png"
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=exe,
            args=args)
        page = browser.new_page(viewport={"width": width, "height": height},
                                device_scale_factor=1)
        page.goto("file://" + os.path.abspath(player_path))
        page.wait_for_function("window.__READY__ === true", timeout=15000)
        import time
        t0 = time.time()
        shot = {"type": "jpeg", "quality": quality, "animations": "disabled",
                "caret": "hide"} if fmt == "jpg" else {"animations": "disabled", "caret": "hide"}
        for i in range(n):
            t = i / fps
            page.evaluate("(t) => window.renderFrame(t)", t)
            page.screenshot(path=os.path.join(frames_dir, f"f_{i:05d}.{ext}"), **shot)
            if i % 120 == 0:
                el = time.time() - t0
                log(f"  帧 {i}/{n}  {el:.0f}s  {i / max(el, .01):.1f} fps")
        browser.close()
    return n


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("player")
    ap.add_argument("outdir")
    ap.add_argument("--total", type=float, required=True)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--w", type=int, default=1920)
    ap.add_argument("--h", type=int, default=1080)
    ap.add_argument("--clip", type=float)
    a = ap.parse_args()
    n = render_frames(a.player, a.outdir, a.total, a.fps, a.w, a.h, a.clip)
    print(f"渲染 {n} 帧 → {a.outdir}")
