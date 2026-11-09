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
