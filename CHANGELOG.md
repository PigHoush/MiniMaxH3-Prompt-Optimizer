# H3PromptOptimizer — 更新日志

> 独立 ComfyUI 环境，运行 Qwen3.8-27B-VL GGUF 提示词优化节点。

---

## v1.0.0 — 2026-11-初

### 环境信息
- 根目录：`D:\H3PromptOptimizer\`
- 端口：8199
- Python：`D:\H3PromptOptimizer\python\python.exe`（3.12 / torch+cu130）
- 启动方式：双击 `启动.bat`（自动检测端口占用，已运行则直接打开浏览器）

### 目录结构
```
D:\H3PromptOptimizer\
├── ComfyUI\
│   ├── main.py
│   ├── models\
│   │   └── Q38-27B-G-UD\
│   │       ├── Qwen3.8-27B-UD-Q2_K_XL.gguf   (9.9G)
│   │       ├── Qwen3.8-27B-UD-Q3_K_XL.gguf   (12.5G)
│   │       └── mmproj-Qwen3.8-27B-F16.gguf   (0.9G)
│   └── custom_nodes\
│       └── ComfyUI_H3PromptOptimizer\       ← Qwen 提示词优化节点
│           └── nodes.py
├── engine\
│   ├── h3_prompt_optimizer.py               ← Qwen 引擎主脚本
│   └── config.json
├── python\
├── 工作流\
└── 启动.bat
```

### 功能
- ComfyUI 节点 `H3PromptOptimizer`：输入提示词文本 + 任务类型（T2VA/I2VA/FL2VA/L2VA/REF2VA）+ 可选参考图，调用本地 Qwen3.8-27B-VL GGUF 生成 H3 规范提示词
- HTTP 接口 `POST /h3_optimize`：body 为 `{text, task, output_language, images_b64, duration, max_tokens}`
- 子进程方式运行，不常驻显存，跑完自动释放

---

## v2.0.0 — 2026-11-09

### 为什么做这个更新

之前的版本（截图所示）需要拖一堆 LoadImage、LoadVideo、LoadAudio 节点，每个素材单独连线到 H3PromptOptimizer 的输入口。9 张参考图就要拖 9 个图片节点、拉 9 根线，再加 3 个视频节点、3 个音频节点，整个画布密密麻麻，管理素材极其麻烦。

这次把所有素材上传整合进节点自身的面板里——一个节点就是一个完整的工作台，不需要外接任何 LoadImage/LoadVideo/LoadAudio，点节点里的"+选图"直接从电脑选文件上传，图显示缩略图、视频能播放、音频能试听。

### 节点面板改造

- **自包含素材面板**：节点内嵌 HTML 面板（addDOMWidget），左边素材网格 + 右边提示词输入框，两栏并排
- **9 图 + 3 视频 + 3 音频上传格**：点"+选图"弹出系统文件选择器，上传到 ComfyUI input 目录后自动显示缩略图/播放器
- **不再外接 LoadImage/LoadVideo/LoadAudio**：素材路径存在节点内部的 `ref_data` JSON 字段里，不连线
- **隐藏了原生 text 和 ref_data 输入框**：用面板里的 textarea 和 JSON 字段替代
- **去掉了左侧所有输入连接点**：`node.inputs = []`，节点左边干干净净

### 按模式动态显示素材格

节点根据"模式"下拉选择，自动显示对应数量的素材上传格：

| 模式 | 图片 | 视频 | 音频 | 说明 |
|------|------|------|------|------|
| T2VA（文生视频） | 0 | 0 | 0 | 只要提示词 |
| I2VA（图生视频） | 1 | 0 | 0 | 1张参考图 |
| L2VA（尾帧视频） | 1 | 0 | 0 | 1张尾帧图 |
| FL2VA（首尾帧） | 2 | 0 | 0 | 首帧+尾帧，上下排列 |
| REF2VA（多主体参考） | 9 | 3 | 3 | 完整素材网格 |
| HYBRID（混合） | 9 | 3 | 3 | 同 REF2VA |
| V2VA（视频转视频） | 0 | 1 | 0 | 1段参考视频 |
| RV2VA（参考改视频） | 9 | 1 | 3 | 9图+1视频+3音频 |

切换模式时面板自动重新渲染，不需要重启。

### 直通输出口

节点右边新增素材输出口，上传的素材可以直接连下游生成节点：
- **优化后的提示词**（STRING）
- **保存路径**（STRING）
- **时长**（FLOAT）— 下游需要时长参数的节点直接连
- **参考图1~9**（IMAGE tensor）— 自动从文件加载为 ComfyUI 标准图像格式
- **参考视频1~3**（STRING 路径）
- **参考音频1~3**（STRING 路径）

### 界面中文化

所有参数标签改为中文显示：模式、时长(秒)、输出语言、最大输出字数、模型。

### 技术要点

- 素材数据存在单个 `ref_data` STRING 字段（JSON 格式 `{"images":[],"videos":[],"audios":[]}`），不用多个 widget
- 文件上传走 ComfyUI 原生 `/upload/image` 接口，预览走 `/view?filename=...&type=input`
- 图片直通用 PIL 加载转 torch tensor `[1,H,W,C]` float32/255
- 左侧输入口通过 JS `node.inputs = []` 清空
- Nodes 2.0 兼容：多次延迟重试隐藏原生 widget DOM

---

## v2.1.0 — 2026-11-13

### 新增：MiniMax-H3-Image 文生图 / 图片编辑

对齐 MiniMax 官方新开源的 H3-Image 提示词写作规则（`skills/h3-image-prompt-writing`），在同一个节点里新增两个图片模式：

| 模式 | 图片 | 视频 | 音频 | 说明 |
|------|------|------|------|------|
| **T2I**（文生图） | 0 | 0 | 0 | 只要提示词，无参考图 |
| **IMG_EDIT**（图片编辑） | 9 | 0 | 0 | 最多 9 张参考图，改图/合成/重风格 |

### 实现方式

- 新增 `engine/image_prompts.py`，把官方 `references/t2i-en.txt` 和 `references/edit-en.txt` 的写作规则浓缩成系统提示词
- 在 `h3_prompt_optimizer.load_optimizer()` 里 monkey-patch vendor 的 `_system_prompt`：task 是 `T2I`/`IMG_EDIT` 时走图片规则，其他任务原封不动走视频六段式
- 视频模式、素材面板、Qwen-VL 推理管线全部复用，不重复造轮子
- 面板 `MODE_CFG` 加两行，T2I 只显示提示词框，IMG_EDIT 显示 9 图槽位（无视频/音频）

### 写作规则差异（图片 vs 视频）

- **T2I**：单张凝固瞬间的成品描述，按"用途 → 布局 → 主体动作 → 可见风格细节 → 画面文字"顺序写；没要求字就显式声明 no text
- **IMG_EDIT**：单段连续文字，按"源定义 `<Subject N>` → 目标概述 → 每个 Subject 的保留/部分保留/属性迁移/弱参考关系 → 改动细节"顺序写
- 画面描述统一用英文（官方建议，H3-Image 在英文提示词上表现最好），画面里的文字保留原语言

### 不做的事

- 不内置出图 API（保留 Optimizer 定位：只优化提示词，渲染交给下游 ComfyUI H3-Image 节点或 `scripts/generate.py`）
- 不改视频模式任何行为

---

## v2.2.0 — 2026-11-13

### 新增：ComfyUI_H3ImageRenderer 出图节点

在 `ComfyUI/custom_nodes/` 下新建 `ComfyUI_H3ImageRenderer/`，直接调 MiniMax H3-Image API 出图，和优化器节点首尾相接。

| 参数 | 说明 |
|------|------|
| prompt | 接优化器"优化后的提示词"输出（STRING） |
| reference_images | 接优化器"参考图1~9"（IMAGE tensor）；不连就是文生图，连了自动走图片编辑 |
| aspect_ratio | 1:1 / 3:2 / 2:3 / 4:3 / 3:4 / 16:9 / 9:16 / 21:9 / 9:21 / 3:1 / 1:3，默认 3:4 |
| area | 4K / 2K / 1K，默认 4K |
| n | 一次出几张（1-10） |
| enhance | 文生图时是否让 API 扩展提示词（默认关，按优化器写的原文渲染） |
| api_base | 国内默认 `https://api.minimax.cn`，海外改 `https://api.minimax.io` |
| api_key | 填 MiniMax key，留空读环境变量 `MINIMAX_API_KEY` |

### 工作流

```
[MiniMax H3 提示词优化器]                    [MiniMax H3 出图]
  模式 = T2I   → 优化后的提示词 ──────────→ prompt
  模式 = IMG_EDIT → 优化后的提示词 ───────→ prompt
                    参考图1~9 ────────────→ reference_images
                                                  ↓
                                               图像输出 → 预览/保存
```

### 技术要点

- 纯 Python 标准库 + ComfyUI 自带的 torch/PIL，无额外依赖
- 参考图：ComfyUI IMAGE tensor `[B,H,W,C]` float32 → JPEG base64 → `data:image/jpeg;base64,...` 发给 API
- 返回的 URL 下载后用 PIL 转 tensor `[1,H,W,C]`，多张拼接成 batch
- 无参考图走 `/v1/images/generations`（默认 `disable_prompt_enhanced=true`），有参考图走 `/v1/images/edits`
- 超时 900 秒，错误信息直接抛到 ComfyUI 黑窗
- `IS_CHANGED` 返回 `nan`，每次都重新生成

### 目录结构（更新后）

```
ComfyUI/custom_nodes/
├── ComfyUI_MiniMaxH3PromptOptimizer/   ← 提示词优化节点（v2.1.0）
└── ComfyUI_H3ImageRenderer/            ← 出图渲染节点（v2.2.0 新增）
    ├── __init__.py
    └── nodes.py
```


