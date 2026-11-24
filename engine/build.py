#!/usr/bin/env python3
"""主流程：剧本 JSON → 配音 → 时间轴 → 逐帧渲染 → 混音 → MP4

  .venv/bin/python engine/build.py content/lidong.json
  .venv/bin/python engine/build.py content/lidong.json --clip 25      # 先渲前 25 秒试片
  .venv/bin/python engine/build.py content/lidong.json --skip-tts     # 只重渲画面
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import tts_edge      # noqa: E402
import bgm           # noqa: E402
import render        # noqa: E402

SR = 44100
VOICE_LEAD = 0.15     # 每段旁白相对场景起点延后一点，避免卡在转场


def run(cmd):
    subprocess.run(cmd, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def dur_of(p):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout
    return float(out.strip())


def synth(text, dst_wav, voice_cfg):
    mp3 = dst_wav.with_suffix(".mp3")
    eng = voice_cfg.get("engine", "edge")
    if eng == "edge":
        tts_edge.synth(text, str(mp3),
                       voice_cfg.get("name", tts_edge.DEFAULT_VOICE),
                       voice_cfg.get("rate", "+0%"),
                       voice_cfg.get("pitch", "+0Hz"))
    elif eng == "kokoro":
        py = os.path.expanduser("~/tts/kokoro/.venv/bin/python")
        run([py, str(ROOT / "engine" / "tts_kokoro.py"),
             "--text", text, "--out", str(mp3),
             "--voice", voice_cfg.get("name", "zf_xiaobei"),
             "--speed", str(voice_cfg.get("speed", 1.0))])
    else:
        raise SystemExit(f"未知配音引擎：{eng}")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3),
         "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(dst_wav)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("--fps", type=int)
    ap.add_argument("--skip-tts", action="store_true")
    ap.add_argument("--skip-render", action="store_true")
    ap.add_argument("--clip", type=float, help="只渲染前 N 秒")
    a = ap.parse_args()

    cfg = json.loads(Path(a.content).read_text(encoding="utf-8"))
    meta = cfg["meta"]
    scenes = cfg["scenes"]
    fps = a.fps or meta.get("fps", 30)
    W, H = meta.get("width", 1920), meta.get("height", 1080)
    lead = meta.get("lead_in", 0.8)
    tail = meta.get("tail", 2.2)

    out = ROOT / "out" / meta["id"]
    audio_dir = out / "audio"
    frames_dir = out / "frames"
    audio_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    print(f"■ 项目：{meta['title']}  场景 {len(scenes)} 个")

    # ---------- 1. 配音 ----------
    wavs, dur = [], []
    for i, sc in enumerate(scenes):
        narr = (sc.get("narration") or "").strip()
        wav = audio_dir / f"seg_{i:02d}.wav"
        if not narr:
            wavs.append(None)
            dur.append(float(sc.get("dur", 3.0)))
            continue
        if a.skip_tts and wav.exists():
            print(f"  [{i:02d}] 复用配音 {narr[:18]}…")
        else:
            print(f"  [{i:02d}] 配音 {narr[:18]}…")
            synth(narr, wav, cfg["voice"])
        wavs.append(wav)
        dur.append(dur_of(wav))
    print(f"  配音完成，总时长 {sum(dur):.1f}s")

    # ---------- 2. 时间轴 ----------
    entries, t = [], lead
    for i, sc in enumerate(scenes):
        pad = float(sc.get("pad", 1.4))
        d = max(dur[i] + pad, 2.6)
        entries.append({
            "index": i,
            "template": sc["template"],
            "props": sc.get("props", {}),
            "narration": sc.get("narration", ""),
            "start": round(t, 3),
            "dur": round(d, 3),
            "audio_dur": round(dur[i], 3),
            "audio": str(wavs[i]) if wavs[i] else None,
        })
        t += d
    total = round(t + tail, 3)

    tl = {"meta": {**meta,
                   "subtitles": meta.get("subtitles", True),
                   "fps": fps, "width": W, "height": H},
          "total": total, "scenes": entries}
    (out / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    (out / "timeline.js").write_text(
        "window.__TIMELINE__ = " + json.dumps(tl, ensure_ascii=False) + ";\n",
        encoding="utf-8")
    for f in ("player.html", "style.css", "scenes.js"):
        shutil.copy2(ROOT / "templates" / f, out / f)
    print(f"■ 时间轴：{total:.2f}s（{int(round(total * fps))} 帧）")

    # ---------- 3. 混音 ----------
    n = int(total * SR) + SR // 2
    voice = np.zeros(n, dtype=np.float32)
    for e in entries:
        if not e["audio"]:
            continue
        data, sr = sf.read(e["audio"], dtype="float32", always_2d=False)
        if sr != SR:
            raise SystemExit(f"采样率不一致：{e['audio']} {sr}")
        i0 = int((e["start"] + VOICE_LEAD) * SR)
        m = min(len(data), n - i0)
        if m > 0:
            voice[i0:i0 + m] += data[:m]

    music, _ = bgm.make(total, seed=int(meta.get("bgm_seed", 11)))
    st = np.stack([voice, voice], axis=1)
    gain = float(meta.get("bgm_gain", 0.085))
    k = min(len(st), len(music))
    st[:k] += music[:k] * gain

    # 整体增益：教室音箱/手机外放偏小，默认 +3dB
    db = float(meta.get("voice_gain_db", 3.0))
    if db:
        st *= 10 ** (db / 20.0)

    peak = float(np.abs(st).max())
    target = float(meta.get("peak_target", 0.89))   # 留 1dB 余量给 AAC
    if peak > target:
        st *= target / peak
        peak = target
    sf.write(out / "mix.wav", st.astype(np.float32), SR)
    print(f"■ 混音完成：peak {20 * np.log10(max(peak, 1e-6)):.1f} dBFS")

    # ---------- 4. 渲染 ----------
    if not a.skip_render:
        print("■ 逐帧渲染中（可中断后重跑，已渲帧会保留）…")
        for f in frames_dir.glob("f_*.png"):
            f.unlink()
        nframes = render.render_frames(
            str(out / "player.html"), str(frames_dir), total, fps, W, H,
            clip=a.clip)
        print(f"■ 渲染完成：{nframes} 帧，用时 {time.time() - t_start:.0f}s")
    else:
        nframes = len(list(frames_dir.glob("f_*.png")))

    # ---------- 5. 编码 ----------
    if nframes == 0:
        print("\n⚠ 没有帧可编码（可能用了 --skip-render），已停在混音步骤。")
        return
    dst = out / f"{meta['id']}.mp4"
    dur_out = min(total, a.clip) if a.clip else total
    run(["ffmpeg", "-y", "-v", "error",
         "-framerate", str(fps), "-i", str(frames_dir / "f_%05d.png"),
         "-i", str(out / "mix.wav"),
         "-t", f"{dur_out:.2f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(dst)])

    # ---------- 6. 联系表（自检用） ----------
    sheet = out / "sheet.jpg"
    try:
        step = max(1, nframes // 12)
        run(["ffmpeg", "-y", "-v", "error", "-i", str(frames_dir / "f_%05d.png"),
             "-vf", f"select='not(mod(n\\,{step}))',scale=480:-2,"
                    "tile=4x3:padding=8:margin=8:color=white",
             "-frames:v", "1", str(sheet)])
    except subprocess.CalledProcessError:
        pass

    size_mb = dst.stat().st_size / 1024 / 1024
    print(f"\n✔ 成片：{dst}  {dur_out:.1f}s  {size_mb:.1f}MB")
    if sheet.exists():
        print(f"✔ 联系表：{sheet}")
    print(f"✔ 用时 {(time.time() - t_start) / 60:.1f} 分钟")


if __name__ == "__main__":
    main()
