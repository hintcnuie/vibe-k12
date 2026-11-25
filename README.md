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
│   ├── lidong.json     # 立冬（语文/节气）
│   ├── lucheng.json    # 路程·时间·速度（横版 16:9，167s）
│   ├── sudu.json       # 路程·时间·速度（竖版 3:4，86.7s，课本 P79–P80）
│   └── xiangyu.json    # 相遇问题（竖版 3:4，超出课本，练习用）
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
├── docs/
│   ├── scripts/           # 讲稿文字版（每期一个 JSON：画面文字+旁白+课本出处）
│   │   └── sudu.json
│   ├── lucheng-lesson.md  # 课本梳理 + 讲稿 + 易错点
│   └── storyboard.md      # 立冬分镜
└── .venv               # 项目环境
```

## 已有成片

| 片子 | 内容 | 时长 | 脚本 |
|---|---|---|---|
| `out/lidong/lidong.mp4` | 立冬（二十四节气） | 78.6s | `content/lidong.json` |
| `out/lucheng/lucheng.mp4` | 路程·时间·速度（四上数学） | 167.3s | `content/lucheng.json` |
| `out/xiangyu/xiangyu.mp4` | 相遇问题（超出课本，仅作练习；竖版 3:4 · 童趣主题） | 68.9s | `content/xiangyu.json` |
| `out/sudu/sudu.mp4` | 路程·时间·速度（人教版四上 P79–P80 · 竖版 3:4 · 童趣主题） | 86.7s | `content/sudu.json` |

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
| `cover` | 封面大标题 + 印章（可选 `size` 覆盖字号，长标题防换行） | `kicker` `title` `sub` `seal` `corner` `size` |
| `seasons_pie` | 大圆切成四块披萨扇形，逐块旋转生长，末块描红弧 | `head` `items[{t,s}]` `active` |
| `seasons` | 四个圆环并列（早期版，保留兼容） | `items[{t,s}]` `active` |
| `statement` | 两行大字陈述 + 脚注 | `lines[]` `foot` |
| `bigchar` | 超大单字 + 拼音 + 释义 + 对照条目 | `char` `pinyin` `gloss` `pairs[{k,v}]` |
| `quote` | 竖排引文 + 出处 | `lines[]` `source` |
| `compare` | 左右两栏对比 | `left{title,items[]}` `right{...}` |
| `timeline` | 横轴四节点，可高亮 | `points[]` `active` `badge` `fact` |
| `ritual` | 左标题 + 右三步流程 | `title` `steps[{n,t}]` |
| `food` | 圆角卡片（3~4 张），图标 + 名称 + 说明 | `title` `items[{e,n,d}]` `note` |
| `table` | 成绩表：表头 + 数据行，可高亮 | `title` `cols[]` `rows[{cells[],hl}]` `note` |
| `formula` | 三词公式，逐块落下，每项带释义 | `a` `b` `c` `op` `ca` `cb` `cc` `note` |
| `motion` | 路面 + 小车匀速行驶 + 时间/路程/速度实时读数 | `v` `path` `tMax` `unitT` `unitD` `title` `note` |
| `ratio` | 关系三角：路程在顶，速度×时间在下，三个变形公式 | `top` `left` `right` `formulas[]` `note` |
| `meet` | 相遇演示（竖版专用）：两人相向匀速前进 + 合走进度条 + 相遇闪光 | `title` `len` `v1` `v2` `n1` `n2` `sumText` |
| `card` | 结尾知识卡（定格收藏）：序号条目 + 脚注 | `title` `items[]` `foot` |
| `outro` | 结尾三行 + 落款印章 | `lines[]` `tag` |

要加新模板：在 `templates/scenes.js` 里加一个函数，返回 `{el, update(local,dur)}`，
并在 `style.css` 加样式。**update 必须是纯函数**——给定时间 t 画面状态唯一确定，
否则就不能任意跳帧、不能断点续渲。

## 竖版（小红书 3:4）与童趣主题

一条片子要出竖版，**只改 `meta`，不动模板**：

```json
"meta": { "theme": "kids", "width": 1080, "height": 1440 }
```

- `player.html` 读 `meta`：`theme` → `body.theme-kids`（亮色板），`height > width` → `body.portrait`。
- 所有竖版差异都写在 `style.css` 末尾的 `body.portrait ...` 覆盖里：字号放大、`compare` 改竖排两卡、`formula` 改上下两行、`ratio` 放大画布，横版数值一律不动。
- **坑**：`scenes.js` 在 player 注入 class 之前就已执行，模板里判断方向必须用 `isPortrait()`（调用时再读 class），不能在模块顶层存常量。
- 模板硬编码 1920×1080 坐标系的（`motion`、`meet`）在 1080 宽画幅下会溢出；`meet` 已按 1080×1440 重写，`motion` 目前仍是横版专用。

童趣主题色板（`theme-kids`）：天空蓝底 `#EDF7FF` + 四角暖黄/薄荷/天蓝/珊瑚色光斑 + 圆点网格；
墨色 `#123A5A`、珊瑚 `#FF5B5B`、薄荷 `#16C79A`、天蓝 `#2E8BF0`、暖黄 `#FFC53D`。
原来的土黄纸感（`paper`）只留给节气/古诗类，K12 数学、儿童向内容一律用 `kids`。

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
- **凡是要表达"匀速/比例"的运动模板，时间轴必须线性**（`update(l, dur)` 里用 `p(l, s, d)` 而不是 `eo`），
  缓动会把匀速画成变速，数值和位移就对不上了。`motion` 模板即按此实现：`d = v × t`，位置由 `d` 反算。
- 数值实时变化的模板（`motion` 的读数），数字用 `toFixed` 收敛，避免亚像素抖动。

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

## 平台发布规范（抖音 / 小红书 / B 站）

同一条片子投三个平台，要求完全不同。**下面这张表是生成内容前的检查依据**，不是发完再补。

| 维度 | 抖音 | 小红书 | B 站 |
|---|---|---|---|
| 分发逻辑 | 推荐流，完播率定生死 | 搜索 + 封面点击 + 收藏 | 搜索 + 知识区推荐，吃深度 |
| 视频比例 | 9:16 竖版最好；16:9 可发但占位小 | **3:4（1080×1440）**最好 | 16:9 横版，现有成片直接用 |
| 时长 | **60–90s**（2:47 偏长） | 60–90s；图文笔记权重更高 | 2:47 可留，**3–5 分钟更好** |
| 标题 | 口语 + 反常识，≤20 字，埋“四年级数学” | ≤20 字，**必须埋搜索词**；封面标题与笔记标题分开 | 25–30 字，反差 / 直给 / 制作向 |
| 封面 | 竖版大字 ≤6 字 | **3:4 竖版**，大字 + 副标题 | 16:9，大字 + 分区角标 |
| 开头 | **3 秒内给结论** | 3 秒内戳痛点（“娃会背公式却不会用”） | 5 秒内抛问题（“谁先到？”） |
| 结尾引导 | “完整版在主页” | “**存下来，下次还能用**”（指向收藏） | “三连 + 下期预告” |
| 必备配套件 | 切片 + 合集 | **图文笔记 + 可截图知识卡** | 章节 + CC 字幕 + 专栏长文 |
| 主角人设 | 家长（提分焦虑） | 妈妈（辅导场景） | 学生 / 成年人自己 |

### 三个平台的具体打法

**抖音**
1. 主发 60–90s 切片：把“两种比法都能用 → 两样都不同就比不了 → 80 对 70”压成 1 分钟，结尾“完整版在主页”。
2. 完整版放合集吃长尾。
3. 开头 3 秒先给结论（“速度不是公式，是 1 分钟走多远”），别用封面大字开场。
4. 封面大字 ≤6 字。

**小红书**
1. **先图文、后视频**：图文权重高于视频，且这套画面天生适合截图。
2. 图文 = 1 张 3:4 封面 + 6 张知识卡（成绩表 / 两种比法 / 80 vs 70 / 公式 / 三角图 / 易错点），正文 300 字。
3. 视频结尾定格 3 秒“三角图 + 三句口诀”知识卡，这是收藏钩子。
4. 字号整体放大：手机上 27px 的注释看不清，正文级文字 ≥32px。
5. 看数据决定是否做视频：**收藏率高 = 选题成立**。

**B 站**
1. 画面基本不用动，主要是**加内容**：加一屏单位换算（60 千米/时 = 1 千米/分），复用 `motion` 改两个参数即可。
2. 开头换成“问题”（松鼠 4 分 280 米 vs 小兔 3 分 240 米，谁快？），别用封面淡入。
3. 结尾改成“下一期：相遇问题”，靠系列养订阅。
4. 章节切成 4 段（比不了 / 先归一 / 速度是什么 / 三个量的关系），时间点从 `timeline.json` 导。
5. 旁白已在时间轴里，可直接导 SRT 挂 CC 字幕（B 站搜索会吃字幕文本）。
6. 投**知识区 → 校园学习**，声明“自制”。

### 三个平台通用的红线（不随平台变）

1. **必须主动勾选“含有 AI 生成内容”标签**。现在发布是必选环节，不选发不出；主动声明不影响分发，被检测出未声明才会打“疑似 AI”警示。
2. **不卖 K12 学科类课程**（数学思维、奥数、速算都算学科类）；不挂学科类小程序，挂教育类小程序的直播间必须真人教学。
3. 不写“提分 / 包会 / 名师”，视频内不出现微信、二维码、群号（导流本身违规）。
4. 不用“最 / 第一 / 百分百”这类极限词，也不用编造“90% 孩子”这类数据。

### 改版式的工作量（重要）

所有模板按 **1920×1080 绝对坐标**排版，**不是裁切就能变竖版**：

- **B 站**：零改动，现有 `out/<id>/<id>.mp4` 直接用。
- **抖音 9:16**：需要竖版版式（重排模板）。
- **小红书 3:4**：同样需要重排；**折中方案是先只做 3:4 竖版封面 + 横屏视频**，成本最低、先把点击率拉起来。

## 已知约束

- **无独显的 Intel Mac**：逐帧截图约 2.9 fps，1 分钟片 ≈ 9 分钟渲染；4 分钟片 ≈ 35 分钟。用 `--clip` 先试。
  WebGL 可用（ANGLE Metal 走集显），但复杂 3D 场景会掉到 1~2 fps。
- Playwright 版本需与已缓存的 Chromium 匹配；`render.py` 会自动扫描 `~/Library/Caches/ms-playwright` 找可执行文件，也可用环境变量 `VK12_CHROMIUM` 指定。
- 字体依赖 macOS 自带：宋体 `Songti SC`、楷体 `Kaiti SC`、黑体 `PingFang SC`。换平台要改 `style.css` 的 `--serif/--sans/--kai`。
- 字幕安全区：底部 200px 留给旁白字幕，其他元素不要压进这个区。
