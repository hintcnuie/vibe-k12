# vibe-k12 · K12 知识动画生产线

把「一份剧本」变成「一条逐帧渲染的知识动画」。画面不是视频模型生成的，而是
**Agent 写代码 → 无头浏览器按时间码渲染 → ffmpeg 合成**，所以字幕不会错字、
公式排版精准、改一个字重渲一段就行。

![preview](docs/preview.jpg)

示例成片：立冬（10 屏 / 78 秒 / 1080P30），分镜稿见 [docs/storyboard.md](docs/storyboard.md)。

## 安装

依赖：Python 3.10+、ffmpeg、Playwright 的 Chromium。

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium   # 已有浏览器可跳过
```

`render.py` 会自动在 `~/Library/Caches/ms-playwright` 下找 Chromium，
也可用环境变量 `VK12_CHROMIUM` 指定路径。

## 目录

```
vibe-k12/
├── content/            # ★ 只改这里：每期一个 JSON
│   └── lidong.json
├── engine/
│   ├── build.py        # 主流程（配音→时间轴→渲染→混音→编码）
│   ├── tts_edge.py     # edge-tts 配音（在线合成，少年音）
│   ├── tts_kokoro.py   # Kokoro 离线配音（断网兜底）
│   ├── bgm.py          # 程序化配乐（五声音阶，零版权）
│   ├── render.py       # Playwright 逐帧截图
│   └── snap.py         # 任意时间点截图，用来快速查版式
├── templates/
│   ├── player.html     # 播放器：把时间轴变成 DOM
│   ├── style.css       # 视觉系统：色板/字体/版式
│   └── scenes.js       # 场景模板库
├── out/<id>/           # 产物：mp4、mix.wav、frames、timeline.json、sheet.jpg
└── .venv               # 项目环境
```

## 跑一条片子

```bash
cd vibe-k12

# 整片
.venv/bin/python engine/build.py content/lidong.json

# 整片，帧用 JPEG 存（默认，比 PNG 快 3.5 倍，画质实测 PSNR 52.6dB）
.venv/bin/python engine/build.py content/lidong.json --fmt jpg

# 不请求独显（A/B 对比用）
.venv/bin/python engine/build.py content/lidong.json --no-dgpu

# 先渲 20 秒试片（改版式时用这个，别整片跑）
.venv/bin/python engine/build.py content/lidong.json --clip 20

# 只重渲画面（配音已生成过）
.venv/bin/python engine/build.py content/lidong.json --skip-tts

# 只看某几个时间点的版式
.venv/bin/python engine/snap.py out/lidong 12 30 46 63
```

产物在 `out/<id>/`：`<id>.mp4`、`mix.wav`、`frames/`、`timeline.json`、`sheet.jpg`（联系表）。

## 换一期内容 = 换一个 JSON

新建 `content/xxx.json`，结构固定，**不用碰代码**：

```json
{
  "meta":  { "id": "xxx", "title": "...", "fps": 30,
             "width": 1920, "height": 1080,
             "lead_in": 0.8, "tail": 2.4, "bgm_gain": 0.085 },
  "voice": { "engine": "edge", "name": "zh-CN-YunxiaNeural",
             "rate": "+6%", "pitch": "+12Hz" },
  "scenes": [
    { "template": "cover",
      "narration": "旁白文本",
      "pad": 1.6,
      "props": { "title": "...", "sub": "..." } }
  ]
}
```

- `narration`：这一屏的旁白。**场景时长 = 旁白时长 + pad**，自动算时间轴，不用手调。
- `pad`：旁白说完后多停留几秒，给画面呼吸。
- 不写 `narration` 时用 `dur` 指定固定秒数。
- 换配音引擎：`"engine": "kokoro"`，`name` 改成 `zf_xiaobei` 之类（见下）。

## 可用的场景模板

| template | 画面 | 主要 props |
|---|---|---|
| `cover` | 封面大标题 + 印章 | `kicker` `title` `sub` `seal` `corner` |
| `seasons_pie` | 大圆切成四块披萨扇形，逐块旋转生长，末块描红弧 | `head` `items[{t,s}]` `active` |
| `seasons` | 四个圆环并列（早期版，保留兼容） | `items[{t,s}]` `active` |
| `statement` | 两行大字陈述 + 脚注 | `lines[]` `foot` |
| `bigchar` | 超大单字 + 拼音 + 释义 + 对照条目 | `char` `pinyin` `gloss` `pairs[{k,v}]` |
| `quote` | 竖排引文 + 出处 | `lines[]` `source` |
| `compare` | 左右两栏对比 | `left{title,items[]}` `right{...}` |
| `timeline` | 横轴四节点，可高亮 | `points[]` `active` `badge` `fact` |
| `ritual` | 左标题 + 右三步流程 | `title` `steps[{n,t}]` |
| `food` | 三张圆角卡片 | `title` `items[{e,n,d}]` `note` |
| `outro` | 结尾三行 + 落款印章 | `lines[]` `tag` |

要加新模板：在 `templates/scenes.js` 里加一个函数，返回 `{el, update(local,dur)}`，
并在 `style.css` 加样式。**update 必须是纯函数**——给定时间 t 画面状态唯一确定，
否则就不能任意跳帧、不能断点续渲。

## 视觉设计规范（本机实测结论）

这一节是「画面怎么做才不单调」的结论汇总，全部在 Intel Mac + 无头 Chromium 上实测过。
新脚本可以直接照这套方案出分镜，不用再重新试错。

### 1. 三层表现策略

| 层 | 用什么 | 覆盖范围 | 性能成本 |
|---|---|---|---|
| **L1 基础层** | SVG 图形 + `transform/opacity/clip-path` | 90% 的画面 | 几乎为 0 |
| **L2 图标层** | 内联 SVG 图标（Lucide/Tabler/Phosphor） | 条目点缀、类别符号 | 0（内联，不装 npm） |
| **L3 3D 层** | Three.js，单 canvas、局部区域 | 仅"必须有空间感"的 1–2 个镜头 | 帧率 −20%~30% |

原则：**能用 L1 解决就不要上 L3**。这套片子的信息密度靠排版和运动过程，不靠立体感。

### 2. 图标与 emoji：能用，但只当点缀

实测：`🍂 ❄️ 🌱 ☀️ 🐿️ 🧣` 六个 emoji 在无头 Chromium 里**全部彩色正常渲染**，
`document.fonts.check('90px "Apple Color Emoji"')` 返回 true，没有 fallback 成黑白方块。

但有四条硬限制，决定了它只能做配角：

1. **是彩色位图字体，不是矢量**——超过 ~120px 明显发虚，细节丢失。
2. **跨平台不一致**——Apple / Segoe / Noto 三套字形，别人 clone 仓库复现会变样（成片栅格化后不影响观众）。
3. **语义漂移**——同一 emoji 在不同系统、不同年代设计会变，不适合承担图解功能。
4. **授权模糊**——作为字体渲染进视频一般无碍，但把图形当素材分发有风险。

**更推荐：内联 SVG 图标集。**

| 库 | 授权 | 风格 | 适合 |
|---|---|---|---|
| **Lucide** | ISC | 线性 1.5px | 最百搭，可做描边生长 |
| **Tabler** | MIT | 线性 2px | 略厚重，小屏清晰 |
| **Phosphor** | MIT | 线性/填充/双色 | 需要"填充版"时用 |

用法：把用到的十几个 SVG 直接内联进模板，`currentColor` 跟随主题色，不引入依赖。

**红线**：单屏图标 ≤ 6 个；单个 ≤ 画面高度 8%（约 86px）；全片只用一套线性风格，不混用。

### 3. Three.js：可行，但要克制

实测无头环境的 WebGL 能力：

```
webgl: true
renderer: ANGLE (Intel, ANGLE Metal Renderer: Intel(R) UHD Graphics 630)
```

是 **ANGLE Metal 硬件加速**，不是 SwiftShader 软件渲染，所以 Three.js 能在这个截图管线里跑。

四条必须遵守的约束：

1. **禁用 `requestAnimationFrame`**——必须由 `update(local)` 手动调 `renderer.render()`，
   并设 `preserveDrawingBuffer: true`，否则截图会拿到上一帧或空白。
2. **依赖变重**——`three` 打包约 1.2MB，会破坏「零依赖克隆即跑」。
3. **确定性下降**——不同 GPU/驱动浮点差异导致逐帧不完全一致，影响可复现，不影响成片。
4. **只做局部**——canvas 建议 960×540 再放大显示，且全片占比 ≤ 10%。

什么时候值得开 3D：地球倾斜 23.5° 绕日、立体几何展开、镜头在场景里推移。
其余 2D 图解一律走 L1，矢量更锐利、渲染更便宜。

### 4. 可纳入的 7 种动效

| # | 动效 | 实现 | 适合的知识类型 | 成本 |
|---|---|---|---|---|
| 1 | **扇形/环形分块揭示** | SVG path + `stroke-dashoffset` 或逐块弹出 | 四季、占比、进度 | 极低 |
| 2 | **路径描边生长** | `stroke-dashoffset` 100%→0 | 迁徙路线、传播路径、轨迹 | 极低 |
| 3 | **数字滚动计数器** | 由 `f(t)` 算数值 | 225°、11月7日、年代 | 极低 |
| 4 | **遮罩擦除转场** | `clip-path` | 换屏、揭开引文 | 极低 |
| 5 | **图形形变 morph** | SVG path 插值 | 芽→叶→果 的演变 | 中 |
| 6 | **沿曲线运动** | `offset-path` + `offset-distance` | 飘落的叶子、飞行轨迹 | 低 |
| 7 | **卡片翻转** | `rotateY` + `backface-visibility` | 正反面对比、谜底揭晓 | 低 |

前四种能把现在的「淡入 + 上浮」升级成「有因果的运动」，优先用。

**注意**：`filter: blur/glow` 这类逐帧重算的滤镜比 3D 还贵，现有模板刻意没用；
`transform/opacity/clip-path` 是合成层操作，几乎免费。

### 5. 性能预算与双显卡实测

本机是 2019 款 16″ MacBook Pro，双显卡（**AMD Radeon Pro 5300M 4GB 独显** + Intel UHD 630 核显）。
实测结论：**Chromium 默认走核显；`--force_high_performance_gpu` 能把它切到独显，但对本项目只值 4%**，
真正的瓶颈是 PNG 无损编码，不是 GPU。

同一段 5 秒、150 帧、1920×1080、完全相同的页面：

| 配置 | ms/帧 | fps | 相对 |
|---|---|---|---|
| 核显 + PNG | 356 | 2.8 | 基准 |
| 独显 + PNG | 341 | 2.9 | +4% |
| 核显 + JPEG q95 | 97 | 10.3 | **3.7×** |
| 独显 + JPEG q95 | 96 | 10.4 | **3.7×** |
| 独显 + JPEG q100 | 114 | 8.7 | 3.1× |

- **GPU 不是瓶颈**：核显→独显在 PNG 与 JPEG 两种抓帧下都只差 1~4ms，说明这一帧的成本在合成与编码，不在光栅化。
- **换掉 PNG 才是关键**：PNG 无压缩编码每帧多花约 250ms。整片实测 **2359 帧：PNG 814 秒 → JPEG 188 秒（4.3×）**。
- **画质够用**：同一帧 PNG vs JPEG(q95) 的 PSNR 是 **52.6 dB**（q100 为 58.8 dB），文字边缘放大对比肉眼无差；
  后续还有 H.264 CRF 18 的二次压缩，JPEG q95 的损失被淹没。所以 `--fmt jpg` 现在就是**默认**。
- **什么时候独显才有用**：加 Three.js / 大画布 / 多层混合的镜头才可能拉开差距，纯 DOM 排版场景没必要为它折腾。
- 开关已内置：`render.py` 的 `high_perf=True`（`build.py` 默认开），关掉用 `--no-dgpu`。
  想确认当前实际用哪张卡：`chrome://gpu` 或 `page.evaluate` 读 `WEBGL_debug_renderer_info`——本项目实测返回 `ANGLE (AMD, Radeon Pro 5300M ...)`。
- `sudo` 类系统级切换（`pmset gpuswitch`）在本机需要密码且**对 Chromium 无效**，别走那条路。

其他开销基线（150 帧小样）：

| 场景 | 实测 | 说明 |
|---|---|---|
| 简单页面纯 DOM | 155ms/帧 | 开销在排版与文字抗锯齿 |
| WebGL 简单场景 | 140ms/帧 | 截图成本与 DOM 几乎一致 |
| + SVG 动效（扇形/描边生长） | 基本不变 | 安全，可随意叠加 |
| + Three.js 简单场景 | −20%~30% | 单个镜头可接受 |
| + 阴影/后处理/大纹理 | < 1 fps | 78 秒片会变 40 分钟，避免 |

结论：**瓶颈是抓帧与编码，不是 3D 能力**；先换帧格式，再考虑复杂度。

### 6. 面向 3–5 年级的红线

- **每屏一个主运动**，最多再配 2~3 个次运动。5 个以上元素同时动会看不过来。
- **不要频闪**：每秒 3 次以上的明暗闪烁有光敏性癫痫风险，平台审核也敏感。
- **缓动统一 `easeOutCubic`**；只有"物质生长"类动作（扇形长出、柱状拔高）允许 ≤10% 的极轻回弹
  （`eBack`，见 `scenes.js`），别用 bounce/elastic 那种大果冻感——在知识片里显廉价。
- **入场 0.6–0.8s，退场 0.3s**，驻留时间 ≥ 旁白时长。
- 字号优先级：屏幕大字 ≥ 64px，说明文字 ≥ 28px，字幕 28px。

### 7. 拿到新脚本 → 分镜稿的套用流程

1. **拆句**：按语义断句，**一句一屏**，每句 ≤ 22 字（超过就拆）。
2. **判形状**：看这一句的"信息形状"，查下表选模板。
3. **定主运动**：每屏只挑一种，从第 4 节里选。
4. **写 JSON**：`narration` 写口语短句，`props` 填屏幕大字；`pad` 给 1.4–1.8 秒。
5. **验收三级**：`snap.py` 抽查单帧 → `--clip 20` 试片 → 整片。

| 信息形状 | 模板 | 主运动 |
|---|---|---|
| 总—分（四类/四季/四段） | `seasons_pie` | 四块扇形依次生长 + 末块红弧高亮（已实现） |
| 单字/概念溯源 | `bigchar` | 竖切揭示（已实现） |
| 一句古文/原文 | `quote` | 逐列自上而下（已实现） |
| 两组对立 | `compare` | 中线生长 + 条目交错（已实现） |
| 时间/序列 | `timeline` | 轴线生长 + 节点依次弹出 + 红色游标走位（已实现） |
| 流程/步骤 | `ritual` | 步骤依次滑入（已实现） |
| 品类/清单 | `food` | 卡片弹入（已实现） |
| 因果链 | 待加 `flow` | 箭头描边生长 |
| 地理/路径 | 待加 `map` | 路径描边生长 |
| 数量对比 | 待加 `bars` | 柱状生长 + 计数器 |

### 8. 新增模板的实现约定

在 `templates/scenes.js` 加一个函数，返回 `{ el, update(local, dur) }`，`style.css` 加样式。必须满足：

- `update` 是**纯函数**：同一 `local` 必出同一画面，不读 `Date.now()`、不用 rAF。
- 只动 `transform / opacity / clip-path`，不用 `filter: blur`。
- 不依赖外部字体与网络资源，图标内联。
- 尺寸用 `vw/vh` 百分比或绝对 px 都可以，但**底部 200px 是字幕安全区**。

## 配音

### 主力：edge-tts（本机生成，合成走微软在线接口）

| 角色 | 音色 | 参数 |
|---|---|---|
| 主讲少年 | `zh-CN-YunxiaNeural` | `--rate=+12% --pitch=+18Hz` |
| 女同学 | `zh-CN-XiaoyiNeural` | `--rate=+8% --pitch=+10Hz` |
| 成年女声 | `zh-CN-XiaoxiaoNeural` | 默认 |
| 低沉男声 | `zh-CN-YunjianNeural` | `--pitch=-8Hz` |

注意：免费端点**没有童声** `zh-CN-XiaoshuangNeural`（Azure 付费专属）。

### 兜底：Kokoro-82M（完全离线）

装在 `~/tts/kokoro/`（`kokoro-v1.0.onnx` 310MB + `voices-v1.0.bin` 27MB + 独立 venv），
中文必须先经 `misaki[zh]`（ZHG2P）注音——它的中文音色就是按这套音素训练的，
直接喂文本会报 `language "zh" is not supported by the espeak backend`。

中文音色 8 个：`zf_xiaobei` `zf_xiaoni` `zf_xiaoxiao` `zf_xiaoyi`
`zm_yunjian` `zm_yunxi` `zm_yunxia` `zm_yunyang`（都是成人声线）。

```bash
~/tts/kokoro/.venv/bin/python engine/tts_kokoro.py --list
~/tts/kokoro/.venv/bin/python engine/tts_kokoro.py --text "测试" --voice zf_xiaobei --out t.wav
```

实测（Intel Mac，CPU）：5.16 秒音频约 6 秒算完（含 3 秒模型加载），≈1 倍实时。
童声化：`ffmpeg -i in.wav -af "rubberband=pitch=1.12" out.wav`

## 已知约束

- **无独显的 Intel Mac**：逐帧截图约 2.9 fps，1 分钟片 ≈ 9 分钟渲染；4 分钟片 ≈ 35 分钟。用 `--clip` 先试。
  WebGL 可用（ANGLE Metal 走集显），但复杂 3D 场景会掉到 1~2 fps。
- Playwright 版本需与已缓存的 Chromium 匹配；`render.py` 会自动扫描 `~/Library/Caches/ms-playwright` 找可执行文件，也可用环境变量 `VK12_CHROMIUM` 指定。
- 字体依赖 macOS 自带：宋体 `Songti SC`、楷体 `Kaiti SC`、黑体 `PingFang SC`。换平台要改 `style.css` 的 `--serif/--sans/--kai`。
- 字幕安全区：底部 200px 留给旁白字幕，其他元素不要压进这个区。
