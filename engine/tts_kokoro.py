#!/usr/bin/env python3
"""Kokoro-82M 离线配音（ONNX / CPU）

必须用 Kokoro 独立环境运行（模型与依赖装在那里，和视频工程的 venv 隔离）：
  ~/tts/kokoro/.venv/bin/python engine/tts_kokoro.py --list
  ~/tts/kokoro/.venv/bin/python engine/tts_kokoro.py --text "..." --voice zf_xiaobei --out x.wav

中文音色是成人声线，需要童声化时在合成后做变调：
  ffmpeg -i in.wav -af "rubberband=pitch=1.12" out.wav
"""
import argparse
import os
import sys

MODEL = os.path.expanduser("~/tts/kokoro/models/kokoro-v1.0.onnx")
VOICES = os.path.expanduser("~/tts/kokoro/models/voices-v1.0.bin")


def load():
    from kokoro_onnx import Kokoro
    return Kokoro(MODEL, VOICES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--out")
    ap.add_argument("--voice", default="zf_xiaobei")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if not (os.path.exists(MODEL) and os.path.exists(VOICES)):
        sys.exit(f"缺少模型文件：\n  {MODEL}\n  {VOICES}")

    k = load()
    if a.list:
        try:
            vs = [v for v in k.get_voices() if v.startswith(("zf_", "zm_"))]
        except Exception:       # noqa: BLE001
            vs = []
        print("中文音色（zf_=女 zm_=男）：")
        for v in vs:
            print("  ", v)
        return

    if not a.text or not a.out:
        sys.exit("需要 --text 和 --out")

    if a.lang.lower().startswith("zh"):
        # Kokoro 中文音色按 misaki 的 ZHG2P 注音训练，必须先转音素
        from misaki.zh import ZHG2P
        g2p = ZHG2P(version="v1.0")
        phon, _ = g2p(a.text)
        samples, sr = k.create(phon, voice=a.voice, speed=a.speed,
                               is_phonemes=True)
    else:
        samples, sr = k.create(a.text, voice=a.voice, speed=a.speed,
                               lang=a.lang)
    import soundfile as sf
    sf.write(a.out, samples, sr)
    print(f"OK {a.out} {len(samples) / sr:.2f}s")

if __name__ == "__main__":
    main()
