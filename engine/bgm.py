#!/usr/bin/env python3
"""程序化生成配乐（五声音阶 / 古风底噪）

好处：完全本地、零版权风险、时长任意、可按片子情绪调整参数。
"""
import numpy as np
import soundfile as sf

SR = 44100


def _pluck(freq, dur, sr=SR):
    n = max(1, int(dur * sr))
    t = np.arange(n) / sr
    env = np.exp(-t * 3.0)
    tone = (0.62 * np.sin(2 * np.pi * freq * t)
            + 0.24 * np.sin(2 * np.pi * freq * 2 * t)
            + 0.09 * np.sin(2 * np.pi * freq * 3 * t))
    attack = np.minimum(1.0, t * 45)
    return (tone * env * attack).astype(np.float32)


def make(duration, seed=11, bpm=62, base_hz=None):
    """返回 (stereo float32 [n,2], sr)"""
    rng = np.random.default_rng(seed)
    base = base_hz or 146.83          # D3
    n = int(duration * SR) + SR
    t = np.arange(n) / SR

    # 低频持续音，慢速起伏
    drone = (0.20 * np.sin(2 * np.pi * (base / 2) * t)
             + 0.09 * np.sin(2 * np.pi * (base / 2 * 1.5) * t))
    lfo = 0.55 + 0.45 * np.sin(2 * np.pi * 0.045 * t)
    out = (drone * lfo).astype(np.float32)

    # 五声音阶拨弦（D 宫：D E F# A B）
    scale = [0, 2, 4, 7, 9]
    beat = 60.0 / bpm
    step = beat * 2
    tt = 0.0
    while tt < duration:
        deg = int(rng.integers(0, 5))
        octv = 2 if rng.random() < 0.7 else 1
        f = base * (2 ** (scale[deg] / 12.0)) * octv
        seg = _pluck(f, min(3.0, duration - tt + 0.6))
        i = int(tt * SR)
        m = min(len(out) - i, len(seg))
        if m > 0:
            out[i:i + m] += seg[:m] * 0.16
        tt += step * (1.0 if rng.random() > 0.3 else 0.5)

    # 两段简单延迟，做出空间感
    for delay_s, amt in ((0.19, 0.28), (0.41, 0.16)):
        d = int(delay_s * SR)
        out[d:] += amt * out[:-d]

    # 裁到目标长度 + 头尾淡入淡出
    n_need = int(duration * SR)
    out = out[:n_need]
    fade = int(1.2 * SR)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)

    peak = float(np.abs(out).max()) or 1.0
    out = out / peak * 0.55

    # 立体声：右声道轻微延迟，制造宽度
    d = int(0.012 * SR)
    right = np.concatenate([np.zeros(d, dtype=np.float32), out[:-d]])
    stereo = np.stack([out, right * 0.9], axis=1).astype(np.float32)
    return stereo, SR


if __name__ == "__main__":
    import sys
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 60
    dst = sys.argv[2] if len(sys.argv) > 2 else "bgm.wav"
    s, sr = make(secs)
    sf.write(dst, s, sr)
    print(f"OK {dst} {secs:.1f}s")
