#!/usr/bin/env python3
"""edge-tts 配音（在线合成，文件落本地）

用法：被 build.py 调用；也可单独测试：
  python engine/tts_edge.py "测试文本" out.mp3
"""
import asyncio
import os
import sys

import edge_tts

DEFAULT_VOICE = "zh-CN-YunxiaNeural"   # 云夏：少年音，适合 3-5 年级


async def _synth(text, out, voice, rate, pitch):
    c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await c.save(out)


def synth(text, out, voice=DEFAULT_VOICE, rate="+0%", pitch="+0Hz", retries=2):
    last = None
    for _ in range(retries + 1):
        try:
            asyncio.run(_synth(text, out, voice, rate, pitch))
            if os.path.getsize(out) > 2000:
                return out
            raise RuntimeError("音频文件为空，可能音色不在免费端点")
        except Exception as e:      # noqa: BLE001
            last = e
    raise RuntimeError(f"edge-tts 合成失败：{last}")


if __name__ == "__main__":
    txt = sys.argv[1]
    dst = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_VOICE
    synth(txt, dst, voice)
    print(f"OK {dst} {os.path.getsize(dst)} bytes")
