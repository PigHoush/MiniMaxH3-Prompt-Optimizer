# -*- coding: utf-8 -*-
"""ComfyUI 独立节点：MiniMax H3 提示词优化器

薄封装：真正的推理由引擎脚本用 D:\\H3PromptOptimizer\\python 起子进程完成。
参考素材通过节点自带 DOM 面板选择（9图+3视频+3音频），不接 LoadImage。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

ENGINE_DIR = Path(r"D:\H3PromptOptimizer\engine")
ENGINE_PY = Path(r"D:\H3PromptOptimizer\python\python.exe")
ENGINE_SCRIPT = ENGINE_DIR / "h3_prompt_optimizer.py"
ENGINE_CONFIG = ENGINE_DIR / "config.json"

TASKS = ["T2VA", "I2VA", "L2VA", "FL2VA", "REF2VA", "HYBRID", "V2VA", "RV2VA"]
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".webm", ".mov", ".mkv", ".avi"}
AUDIO_EXTS = {".wav", ".mp3", ".flac", ".aac", ".m4a"}


def _input_dir() -> Path:
    try:
        import folder_paths
        return Path(folder_paths.get_input_directory())
    except Exception:
        return Path(tempfile.gettempdir())


def _list_media(exts: set[str]) -> list[str]:
    d = _input_dir()
    if not d.is_dir():
        return ["无"]
    out = ["无"]
    for p in sorted(d.iterdir(), key=lambda x: x.name.lower()):
        if p.is_file() and p.suffix.lower() in exts:
            out.append(p.name)
    return out


def _scan_models() -> list[tuple[str, str, str]]:
    try:
        cfg = json.loads(ENGINE_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return []
    out: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for root in cfg.get("model_dirs") or []:
        rp = Path(root)
        if not rp.is_dir():
            continue
        files: list[Path] = []
        for base, _dirs, names in os.walk(str(rp), followlinks=True):
            for n in names:
                if n.lower().endswith(".gguf"):
                    files.append(Path(base) / n)
        files.sort(key=lambda p: str(p).lower())
        for f in files:
            if "mmproj" in f.name.lower():
                continue
            try:
                rel = f.relative_to(rp).as_posix()
            except ValueError:
                continue
            if rel in seen:
                continue
            seen.add(rel)
            mm = ""
            sibs = sorted(
                (p for p in f.parent.iterdir()
                 if p.is_file() and "mmproj" in p.name.lower() and p.suffix.lower() == ".gguf"),
                key=lambda p: str(p).lower(),
            )
            if sibs:
                try:
                    mm = sibs[0].relative_to(rp).as_posix()
                except ValueError:
                    mm = ""
            label = f.stem + (f"  ·  {Path(mm).name}" if mm else "  ·  （无 mmproj）")
            out.append((label, rel, mm))
    return out


MODELS = _scan_models()


class MiniMaxH3PromptOptimizer:

    CATEGORY = "MiniMax H3"
    FUNCTION = "run"
    RETURN_TYPES = (
        "STRING", "STRING", "FLOAT",
        "IMAGE","IMAGE","IMAGE","IMAGE","IMAGE","IMAGE","IMAGE","IMAGE","IMAGE",
        "STRING","STRING","STRING",
        "STRING","STRING","STRING",
    )
    RETURN_NAMES = (
        "优化后的提示词", "保存路径", "时长",
        "参考图1","参考图2","参考图3","参考图4","参考图5","参考图6","参考图7","参考图8","参考图9",
        "参考视频1","参考视频2","参考视频3",
        "参考音频1","参考音频2","参考音频3",
    )
    OUTPUT_NODE = False

    @classmethod
    def INPUT_TYPES(cls):
        labels = [m[0] for m in MODELS] or ["（未找到模型）"]
        return {
            "required": {
                "模式": (TASKS, {"default": "T2VA"}),
                "时长(秒)": ("FLOAT", {"default": 10.0, "min": 1.0, "max": 60.0, "step": 1.0}),
                "输出语言": (["中文", "English"], {"default": "中文"}),
                "最大输出字数": ("INT", {"default": 4096, "min": 512, "max": 8192, "step": 256}),
                "模型": (labels, {"default": labels[0]}),
            },
            "optional": {
                "text": ("STRING", {"multiline": True, "default": "", "dynamicPrompts": False}),
                "ref_data": ("STRING", {"default": "{}", "multiline": False}),
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def run(self, text, **kwargs):
        task = str(kwargs.get("模式", "T2VA")).strip().upper()
        duration = kwargs.get("时长(秒)", 10.0)
        output_language = kwargs.get("输出语言", "中文")
        max_tokens = kwargs.get("最大输出字数", 4096)
        model = kwargs.get("模型", "")
        ref_data = kwargs.get("ref_data", "{}")
        if not str(text or "").strip():
            raise RuntimeError("提示词为空")
        if not ENGINE_PY.is_file():
            raise RuntimeError(f"找不到引擎: {ENGINE_PY}")
        if not ENGINE_SCRIPT.is_file():
            raise RuntimeError(f"找不到脚本: {ENGINE_SCRIPT}")

        task = str(task or "T2VA").strip().upper()
        if task not in TASKS:
            raise RuntimeError(f"任务类型只能是 {', '.join(TASKS)}")

        target = str(model or "")
        rel, mmproj = "", ""
        for label, r, m in MODELS:
            if target == label or target == r or Path(r).name == target:
                rel, mmproj = r, m
                break

        try:
            rd = json.loads(ref_data) if ref_data else {}
        except Exception:
            rd = {}
        ref_imgs = rd.get("images", [])
        ref_vids = rd.get("videos", [])
        ref_auds = rd.get("audios", [])

        work = Path(tempfile.mkdtemp(prefix="h3po_"))
        prompt_file = work / "prompt.txt"
        prompt_file.write_text(str(text), encoding="utf-8")
        out_file = work / "optimized.txt"

        cmd = [str(ENGINE_PY), str(ENGINE_SCRIPT),
               "--prompt-file", str(prompt_file),
               "--out", str(out_file),
               "--task", task,
               "--duration", f"{float(duration):g}",
               "--lang", str(output_language),
               "--max-tokens", str(int(max_tokens))]
        if rel:
            cmd += ["--model", rel]
        if mmproj:
            cmd += ["--mmproj", mmproj]

        in_dir = _input_dir()
        spec = []
        img_idx = 0
        for name in ref_imgs:
            if not name or name == "无":
                continue
            src = in_dir / name
            if not src.is_file():
                continue
            img_idx += 1
            import shutil
            dst = work / name
            shutil.copy2(src, dst)
            spec.append({"label": f"<picture {img_idx}>", "kind": "image",
                         "images": [str(dst)]})

        vid_idx = 0
        for name in ref_vids:
            if not name or name == "无":
                continue
            vid_idx += 1
            spec.append({"label": f"<video {vid_idx}>", "kind": "video",
                         "images": [], "note": f"参考视频: {name}"})

        aud_idx = 0
        for name in ref_auds:
            if not name or name == "无":
                continue
            aud_idx += 1
            spec.append({"label": f"<audio {aud_idx}>", "kind": "audio",
                         "note": f"参考音频: {name}"})

        if spec:
            media_file = work / "media.json"
            media_file.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
            cmd += ["--media-file", str(media_file)]

        print(f"[H3提示词优化] task={task} duration={duration:g}s images={img_idx} videos={vid_idx} audios={aud_idx}")
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900,
                              creationflags=CREATE_NO_WINDOW, encoding="utf-8",
                              errors="replace")
        if proc.returncode != 0 or not out_file.is_file():
            tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-12:]
            raise RuntimeError("提示词优化失败：\n" + "\n".join(tail))
        result = out_file.read_text(encoding="utf-8").strip()
        print(f"[H3提示词优化] 完成，{len(result)} 字符")

        # Passthrough: load images as IMAGE tensors, pass video/audio filenames
        def _load_img_tensor(name):
            try:
                from PIL import Image
                import torch
                import numpy as np
                p = in_dir / name
                if not p.is_file():
                    return None
                img = Image.open(p).convert("RGB")
                arr = np.array(img).astype(np.float32) / 255.0
                return torch.from_numpy(arr).unsqueeze(0)
            except Exception as e:
                print(f"[H3提示词优化] 图片加载失败 {name}: {e}")
                return None

        img_out = [_load_img_tensor(ref_imgs[i]) if i < len(ref_imgs) and ref_imgs[i] else None for i in range(9)]
        vid_out = [(ref_vids[i] if i < len(ref_vids) else None) for i in range(3)]
        aud_out = [(ref_auds[i] if i < len(ref_auds) else None) for i in range(3)]

        return {"ui": {"text": [result]},
                "result": (result, str(out_file), float(duration), *img_out, *vid_out, *aud_out)}


NODE_CLASS_MAPPINGS["MiniMaxH3PromptOptimizer"] = MiniMaxH3PromptOptimizer
NODE_DISPLAY_NAME_MAPPINGS["MiniMaxH3PromptOptimizer"] = "MiniMax H3 提示词优化器"


# HTTP 路由给导演台调用
async def _h3_optimize_handler(request):
    import base64
    from aiohttp import web
    try:
        data = await request.json()
    except Exception as exc:
        return web.json_response({"error": f"invalid JSON: {exc}"}, status=400)
    text = (data.get("text") or "").strip()
    if not text:
        return web.json_response({"error": "empty text"}, status=400)
    task = str(data.get("task") or "T2VA").strip().upper()
    if task not in TASKS:
        mapping = {"T2V": "T2VA", "I2V": "I2VA", "FL2V": "FL2VA",
                   "R2V": "REF2VA", "RV2V": "REF2VA", "L2V": "L2VA"}
        task = mapping.get(task, "T2VA")
    output_language = str(data.get("output_language") or "中文")
    duration = float(data.get("duration") or 10.0)
    max_tokens = int(data.get("max_tokens") or 4096)
    work = Path(tempfile.mkdtemp(prefix="h3http_"))
    prompt_file = work / "prompt.txt"
    prompt_file.write_text(text, encoding="utf-8")
    out_file = work / "optimized.txt"
    cmd = [str(ENGINE_PY), str(ENGINE_SCRIPT),
           "--prompt-file", str(prompt_file), "--out", str(out_file),
           "--task", task, "--duration", f"{duration:g}",
           "--lang", output_language, "--max-tokens", str(max_tokens)]
    imgs = data.get("images_b64") or []
    spec = []
    for idx, b64 in enumerate(imgs, start=1):
        if not b64:
            continue
        if "," in b64 and b64.startswith("data:"):
            b64 = b64.split(",", 1)[1]
        try:
            raw = base64.b64decode(b64)
        except Exception:
            continue
        p = work / f"ref_{idx}.jpg"
        p.write_bytes(raw)
        spec.append({"label": f"<picture {idx}>", "kind": "image", "images": [str(p)]})
    if spec:
        media_file = work / "media.json"
        media_file.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        cmd += ["--media-file", str(media_file)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900,
                          creationflags=CREATE_NO_WINDOW, encoding="utf-8", errors="replace")
    if proc.returncode != 0 or not out_file.is_file():
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-15:]
        return web.json_response({"error": "engine failed", "detail": "\n".join(tail)}, status=500)
    result = out_file.read_text(encoding="utf-8").strip()
    return web.json_response({"text": result})


try:
    from aiohttp import web as _web
    from server import PromptServer
    PromptServer.instance.app.add_routes([_web.post("/h3_optimize", _h3_optimize_handler)])
except Exception as _e:
    import logging as _lg
    _lg.getLogger("ComfyUI-H3PromptOptimizer").warning("route not registered: %s", _e)
