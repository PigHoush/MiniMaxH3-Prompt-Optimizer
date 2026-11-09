# H3PromptOptimizer

独立 ComfyUI 环境，运行 Qwen3.8-27B-VL GGUF 提示词优化节点。可以像普通 ComfyUI 节点一样连线使用，输出优化后的 STRING 给下游。

## 功能

- **开放式节点**：`H3PromptOptimizer` 可连线，接收 STRING 输入 + 参考图/视频/音频，输出优化后的 STRING
- **多模态**：Qwen VL 视觉模型能读取参考图内容，生成带画面描述的提示词
- **任务感知**：支持 T2VA / I2VA / FL2VA / L2VA / REF2VA 等模式
- **时长控制**：可传入目标时长，Qwen 生成匹配节奏的提示词
- **不抢显存**：子进程方式运行，跑完自动退出释放显存

## 安装

### 前置
- 已安装 [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- 需要 llama-cpp-python：`pip install llama-cpp-python`

### 步骤
1. clone 仓库
2. 把 `ComfyUI/custom_nodes/ComfyUI_H3PromptOptimizer` 复制到你的 ComfyUI custom_nodes
3. 配置 `engine/config.json` 里的模型路径
4. 下载 Qwen GGUF 模型放到 `engine/models/`
5. 启动 ComfyUI，在节点列表里搜 H3PromptOptimizer

## 模型

需要自己下载：
- Qwen3.8-27B-UD-Q2_K_XL.gguf（快速版 ~9.9G）
- Qwen3.8-27B-UD-Q3_K_XL.gguf（高质量版 ~12.5G）
- mmproj-Qwen3.8-27B-F16.gguf（视觉投影 ~0.9G）

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)

## 致谢

- [MiniMax H3 Director](https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director) — 导演台
- Qwen3.8 / llama.cpp — 推理引擎
