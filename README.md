# MiniMaxH3-Prompt-Optimizer

ComfyUI 自定义节点，内嵌 Qwen3.8-27B-VL 本地大模型，按 MiniMax H3 视频生成规范自动优化提示词。自包含素材面板（图/视频/音频上传+预览），支持 8 种生成模式动态切换，直通输出素材到下游节点。

## 这是什么

一个节点搞定所有事：上传参考图/视频/音频、输入提示词、一键让 Qwen 优化成 H3 规范格式，优化后的提示词和素材直接连下游生成节点。不需要外接 LoadImage、LoadVideo、LoadAudio，不用在画布上拉一堆线。

## 功能

- **自包含素材面板**：节点内嵌 HTML 面板，左边素材网格 + 右边提示词输入框，点"+选图"直接从电脑选文件
- **8 种模式动态切换**：
  - T2VA（文生视频）— 只要提示词
  - I2VA（图生视频）— 1张参考图
  - L2VA（尾帧视频）— 1张尾帧图
  - FL2VA（首尾帧）— 首帧+尾帧，上下排列
  - REF2VA / HYBRID（多主体参考）— 9图+3视频+3音频
  - V2VA（视频转视频）— 1段参考视频
  - RV2VA（参考改视频）— 9图+1视频+3音频
- **直通输出口**：优化后的提示词(STRING)、保存路径(STRING)、时长(FLOAT)、参考图1~9(IMAGE tensor)、参考视频1~3(STRING路径)、参考音频1~3(STRING路径)
- **全中文界面**：模式、时长(秒)、输出语言、最大输出字数、模型
- **不抢显存**：Qwen 用子进程跑，跑完自动退出，不跟生成模型抢 GPU

## 配套项目

- [MiniMaxH3Director-Qwen-Prompt](https://github.com/PigHoush/MiniMaxH3Director-Qwen-Prompt) — 导演台，集成了本节点的 Qwen 优化能力

## 迭代历程

### v1.0.0 — 多节点连线时代

最初的版本是"裸节点"模式：
- 需要拖 9 个 LoadImage 节点 + 3 个 LoadVideo 节点 + 3 个 LoadAudio 节点
- 每个素材单独连线到 H3PromptOptimizer 的对应输入口
- 画布上密密麻麻全是线，管理素材极其麻烦
- 提示词、任务类型、时长等参数都是 ComfyUI 原生下拉框和输入框

### v2.0.0 — 自包含面板时代

重写了整个前端面板：
- **一个节点就是一个完整工作台**：点节点里的"+选图"直接从电脑选文件，图显示缩略图、视频能播放、音频能试听
- **不再外接任何 LoadImage/LoadVideo/LoadAudio**：素材路径存在节点内部的 JSON 字段里
- **按模式动态显示素材格**：选 T2VA 就只有提示词框，选 REF2VA 才出现 9图3视频3音频网格
- **去掉了所有左侧连接点**：节点左边干干净净，纯面板操作
- **新增直通输出口**：上传的素材直接转成 ComfyUI 标准格式输出到下游，不用再 LoadImage
- **界面全中文化**

## 安装

1. clone 这个仓库
2. 把 `ComfyUI/custom_nodes/ComfyUI_MiniMaxH3PromptOptimizer/` 复制到你的 ComfyUI custom_nodes 目录
3. 把 `engine/` 目录放到方便的位置，改 `engine/config.json` 里的模型路径
4. 需要 llama.cpp 支持的 Qwen GGUF 模型，`.gguf` 丢进 `engine/models/`
5. 安装依赖：`pip install llama-cpp-python`
6. 启动 ComfyUI，搜索"MiniMax H3 提示词优化器"节点

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)

## 致谢

- [MiniMax H3 Director](https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director) — 导演台
- Qwen3.8 / llama.cpp — 推理引擎
