import { app } from "../../scripts/app.js";

const css = `
.h3po-wrap{font-family:system-ui,sans-serif;color:#ccc;padding:4px;font-size:11px;box-sizing:border-box;display:flex;gap:6px;}
.h3po-left{flex:1;min-width:0;display:flex;flex-direction:column;gap:5px;}
.h3po-right{flex:1;min-width:0;display:flex;flex-direction:column;}
.h3po-txt{flex:1;width:100%;background:#1a1d24;border:1px solid #2a3140;border-radius:4px;color:#ccc;padding:8px;font-size:11px;resize:none;box-sizing:border-box;font-family:system-ui;line-height:1.5;min-height:120px;}
.h3po-txt:focus{outline:none;border-color:#4a9eff;}
.h3po-sec{display:flex;flex-direction:column;gap:4px;}
.h3po-sec-t{font-weight:700;font-size:10px;color:#888;display:flex;justify-content:space-between;}
.h3po-c{font-weight:400;opacity:.5;}
.h3po-g{display:grid;gap:4px;}
.h3po-cell{aspect-ratio:4/3;background:#1a1d24;border:1px solid #2a3140;border-radius:4px;overflow:hidden;position:relative;cursor:pointer;}
.h3po-cell:hover{border-color:#4a9eff;}
.h3po-cell img{width:100%;height:100%;object-fit:cover;display:block;}
.h3po-cell video{width:100%;height:100%;object-fit:contain;display:block;background:#000;}
.h3po-cell.aud{aspect-ratio:5/1;display:flex;align-items:center;padding:0 6px;gap:6px;}
.h3po-cell.aud audio{width:100%;height:20px;}
.h3po-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;color:#555;font-size:16px;width:100%;height:100%;gap:2px;}
.h3po-empty small{font-size:8px;}
.h3po-x{position:absolute;top:3px;right:3px;width:16px;height:16px;border-radius:50%;background:rgba(220,50,50,.85);color:#fff;font-size:11px;line-height:16px;text-align:center;cursor:pointer;display:none;z-index:3;}
.h3po-cell:hover .h3po-x{display:block;}
.h3po-nm{position:absolute;bottom:0;left:0;right:0;background:rgba(0,0,0,.7);font-size:7px;padding:2px 4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.h3po-label{font-size:9px;color:#666;text-align:center;margin-top:1px;}
`;

const sid = "h3po-panel-css";
if (!document.getElementById(sid)) {
  const s = document.createElement("style");
  s.id = sid;
  s.textContent = css;
  document.head.appendChild(s);
}

const MODE_CFG = {
  T2VA:    { imgs: 0, vids: 0, auds: 0 },
  I2VA:    { imgs: 1, vids: 0, auds: 0 },
  L2VA:    { imgs: 1, vids: 0, auds: 0 },
  FL2VA:   { imgs: 2, vids: 0, auds: 0 },
  REF2VA:  { imgs: 9, vids: 3, auds: 3 },
  HYBRID:  { imgs: 9, vids: 3, auds: 3 },
  V2VA:    { imgs: 0, vids: 1, auds: 0 },
  RV2VA:   { imgs: 9, vids: 1, auds: 3 },
};

app.registerExtension({
  name: "H3PromptOptimizer.Panel",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "MiniMaxH3PromptOptimizer") return;

    const orig = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      orig?.apply(this, arguments);
      const node = this;

      setTimeout(() => {
        let refW = null, textW = null, taskW = null;
        (node.widgets || []).forEach(w => {
          if (w.name === "ref_data") refW = w;
          if (w.name === "text") textW = w;
          if (w.name === "模式") taskW = w;
        });
        if (!refW) return;

        // Remove all left-side input connection dots (widget-only params)
        node.inputs = [];

        if (refW.element) refW.element.remove();
        refW.type = "hidden"; refW.draw = () => 0; refW.computeSize = () => [0, 0];

        if (textW) {
          if (textW.element) textW.element.remove();
          textW.type = "hidden"; textW.draw = () => 0; textW.computeSize = () => [0, 0];
        }
        setTimeout(() => { if (textW?.element) textW.element.remove(); if (refW?.element) refW.element.remove(); }, 500);
        setTimeout(() => { if (textW?.element) textW.element.remove(); if (refW?.element) refW.element.remove(); }, 1500);

        function getData() { try { return JSON.parse(refW.value || "{}"); } catch { return {}; } }
        function setData(d) { refW.value = JSON.stringify(d); refresh(); }

        const box = document.createElement("div");
        box.className = "h3po-wrap";

        function pickFile(accept, cb) {
          const inp = document.createElement("input");
          inp.type = "file"; inp.accept = accept;
          inp.onchange = async () => {
            const f = inp.files[0]; if (!f) return;
            const fd = new FormData();
            fd.append("image", f); fd.append("type", "input"); fd.append("overwrite", "true");
            try {
              const r = await fetch("/upload/image", { method: "POST", body: fd });
              const d = await r.json();
              if (d.name) cb(d.name);
            } catch(e) { console.error("upload", e); }
          };
          inp.click();
        }

        function makeCell(kind, name, label, onPick, onClear) {
          const c = document.createElement("div");
          c.className = "h3po-cell" + (kind === "audio" ? " aud" : "");
          if (name) {
            if (kind === "image")
              c.innerHTML = `<img src="/view?filename=${encodeURIComponent(name)}&type=input" loading="lazy"><div class="h3po-x">×</div><div class="h3po-nm">${name}</div>`;
            else if (kind === "video")
              c.innerHTML = `<video src="/view?filename=${encodeURIComponent(name)}&type=input" controls preload="metadata"></video><div class="h3po-x">×</div><div class="h3po-nm">${name}</div>`;
            else
              c.innerHTML = `<audio src="/view?filename=${encodeURIComponent(name)}&type=input" controls preload="metadata"></audio><div class="h3po-x">×</div>`;
            c.querySelector(".h3po-x").onclick = (e) => { e.stopPropagation(); onClear(); };
          } else {
            if (kind === "image") c.innerHTML = `<div class="h3po-empty">+<small>${label||'选图'}</small></div>`;
            else if (kind === "video") c.innerHTML = `<div class="h3po-empty">+<small>${label||'视频'}</small></div>`;
            else c.innerHTML = `<div class="h3po-empty" style="font-size:11px">+ 音频</div>`;
          }
          c.onclick = onPick;
          return c;
        }

        function makeSection(parent, title, count, total) {
          const sec = document.createElement("div");
          sec.className = "h3po-sec";
          sec.innerHTML = `<div class="h3po-sec-t">${title}<span class="h3po-c">${count}/${total}</span></div>`;
          const g = document.createElement("div");
          g.className = "h3po-g";
          sec.appendChild(g);
          parent.appendChild(sec);
          return g;
        }

        function refresh() {
          box.innerHTML = "";
          const d = getData();
          const imgs = d.images || [];
          const vids = d.videos || [];
          const auds = d.audios || [];
          const task = (taskW?.value || "T2VA").toUpperCase();
          const cfg = MODE_CFG[task] || MODE_CFG.REF2VA;
          const hasMedia = cfg.imgs > 0 || cfg.vids > 0 || cfg.auds > 0;

          let left = null;
          if (hasMedia) {
            left = document.createElement("div");
            left.className = "h3po-left";

            function gridCols(n) {
              if (n <= 2) return "1fr";
              return "1fr 1fr 1fr";
            }

            if (cfg.imgs > 0) {
              const labels = task === "FL2VA" ? ["首帧", "尾帧"] : [];
              const gi = makeSection(left, "参考图片", imgs.filter((_,i)=>i<cfg.imgs).length, cfg.imgs);
              gi.style.gridTemplateColumns = gridCols(cfg.imgs);
              for (let i = 0; i < cfg.imgs; i++) {
                const name = imgs[i] || "";
                const cellWrap = document.createElement("div");
                cellWrap.appendChild(makeCell("image", name, labels[i] || "选图", () => {
                  pickFile("image/*", (fname) => {
                    const arr = [...imgs]; arr[i] = fname;
                    setData({ ...getData(), images: arr });
                  });
                }, () => {
                  const arr = [...imgs]; arr.splice(i, 1);
                  setData({ ...getData(), images: arr });
                }));
                if (labels[i]) {
                  const lb = document.createElement("div");
                  lb.className = "h3po-label";
                  lb.textContent = labels[i];
                  cellWrap.appendChild(lb);
                }
                gi.appendChild(cellWrap);
              }
            }

            if (cfg.vids > 0) {
              const gv = makeSection(left, "参考视频", vids.filter((_,i)=>i<cfg.vids).length, cfg.vids);
              gv.style.gridTemplateColumns = gridCols(cfg.vids);
              for (let i = 0; i < cfg.vids; i++) {
                const name = vids[i] || "";
                gv.appendChild(makeCell("video", name, "视频", () => {
                  pickFile("video/*", (fname) => {
                    const arr = [...vids]; arr[i] = fname;
                    setData({ ...getData(), videos: arr });
                  });
                }, () => {
                  const arr = [...vids]; arr.splice(i, 1);
                  setData({ ...getData(), videos: arr });
                }));
              }
            }

            if (cfg.auds > 0) {
              const ga = makeSection(left, "参考音频", auds.filter((_,i)=>i<cfg.auds).length, cfg.auds);
              ga.style.gridTemplateColumns = gridCols(cfg.auds);
              for (let i = 0; i < cfg.auds; i++) {
                const name = auds[i] || "";
                ga.appendChild(makeCell("audio", name, "", () => {
                  pickFile("audio/*", (fname) => {
                    const arr = [...auds]; arr[i] = fname;
                    setData({ ...getData(), audios: arr });
                  });
                }, () => {
                  const arr = [...auds]; arr.splice(i, 1);
                  setData({ ...getData(), audios: arr });
                }));
              }
            }
          }

          const right = document.createElement("div");
          right.className = "h3po-right";
          const ta = document.createElement("textarea");
          ta.className = "h3po-txt";
          ta.placeholder = "输入需要优化的提示词...";
          ta.value = textW ? (textW.value || "") : "";
          ta.oninput = () => { if (textW) textW.value = ta.value; };
          right.appendChild(ta);

          if (left) box.appendChild(left);
          box.appendChild(right);

          let h = 140;
          if (cfg.imgs > 0) {
            if (cfg.imgs <= 2) h += cfg.imgs * 60 + 25;
            else h += Math.ceil(cfg.imgs/3) * 60 + 25;
          }
          if (cfg.vids > 0) h += (cfg.vids <= 1 ? 60 : 70);
          if (cfg.auds > 0) h += 50;
          panelWidget.options.getMinHeight = () => h;
        }

        if (taskW) {
          const origCb = taskW.callback;
          taskW.callback = function() { origCb?.apply(this, arguments); refresh(); };
        }

        const panelWidget = node.addDOMWidget("h3po_panel", "div", box, {
          getValue: () => refW.value,
          setValue: (v) => { refW.value = v; refresh(); },
          getMinHeight: () => 300,
          hideOnZoom: false,
        });

        refresh();
      }, 200);
    };
  },
});
