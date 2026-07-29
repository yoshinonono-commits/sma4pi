"""新機能(拡大・任意関数・注釈)の動作確認。GUI 無しで走る。

    python tests/test_features.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent, MouseButton

from sma4py import canvas as cv, model, interaction
from sma4py.model import Document, Series, FunctionCurve, Annotation

# --- 土台 -----------------------------------------------------------------
cv.setup_japanese_font()
np.random.seed(2)
xd = np.linspace(0, 10, 40)
yd = np.sin(xd) + np.random.normal(0, 0.08, 40)

doc = Document()
doc.series.append(Series(name="data", x=xd, y=yd))
doc.functions.append(FunctionCurve(name="sin(x)", expr="sin(x)", auto_range=True))
doc.functions.append(FunctionCurve(name="範囲固定", expr="0.5*cos(2*x)",
                                   auto_range=False, xmin=2, xmax=8, color="#9467bd"))
doc.annotations.append(Annotation(text="頂点", x=1.57, y=1.0, coords="data",
                                  arrow=True, ax_=1.57, ay_=1.0))
doc.annotations.append(Annotation(text="%Iy%R = sin %Ix%R", x=0.05, y=0.95,
                                  coords="axes", va="top"))
doc.config.legend = True

fig = plt.figure(figsize=(6, 4.5), layout="constrained")
ax = fig.add_subplot(111)
canvas = fig.canvas

print("=== 1. 任意関数の重ね書き ===")
fx, fy = doc.functions[0].sample(fallback=cv.data_bounds(doc))
print(f"  auto_range: x範囲={fx.min():.2f}〜{fx.max():.2f} (データは 0.00〜10.00)")
fx2, _ = doc.functions[1].sample(fallback=cv.data_bounds(doc))
print(f"  範囲固定  : x範囲={fx2.min():.2f}〜{fx2.max():.2f} (指定は 2〜8)")
assert abs(fx.max() - 10.0) < 1e-9 and abs(fx2.max() - 8.0) < 1e-9

print("\n=== 2. 描画と注釈 artist ===")
artists = cv.render(doc, ax)
canvas.draw()
print(f"  注釈 artist 数 = {len(artists)}  (1つは矢印付き annotate)")
assert len(artists) == 2

nav = interaction.NavigationHandler(canvas, ax, get_doc=lambda: doc,
                                    on_change=lambda: None, on_status=lambda m: None)
nav.set_artists(artists)

def press(x, y, button=MouseButton.LEFT, dbl=False):
    px, py = ax.transData.transform((x, y))
    e = MouseEvent("button_press_event", canvas, px, py, button, dblclick=dbl)
    nav.on_press(e); return e
def move(x, y, button=None):
    px, py = ax.transData.transform((x, y))
    nav.on_motion(MouseEvent("motion_notify_event", canvas, px, py, button))
def release(x, y, button=MouseButton.LEFT):
    px, py = ax.transData.transform((x, y))
    nav.on_release(MouseEvent("button_release_event", canvas, px, py, button))

print("\n=== 3. 左ドラッグで範囲拡大 ===")
press(2.0, -0.5); move(6.0, 0.8); release(6.0, 0.8)
c = doc.config
print(f"  xauto={c.xauto} x=[{c.xmin:.2f}, {c.xmax:.2f}]  y=[{c.ymin:.2f}, {c.ymax:.2f}]")
assert not c.xauto and abs(c.xmin-2.0)<1e-6 and abs(c.xmax-6.0)<1e-6
assert abs(c.ymin+0.5)<1e-6 and abs(c.ymax-0.8)<1e-6

print("\n=== 4. 小さすぎるドラッグはクリック扱い ===")
before = (c.xmin, c.xmax)
press(3.0, 0.0); move(3.001, 0.001); release(3.001, 0.001)
print(f"  範囲は変わらない: {before == (c.xmin, c.xmax)}")
assert before == (c.xmin, c.xmax)

print("\n=== 5. ダブルクリックで全体表示 ===")
press(4.0, 0.0, dbl=True)
print(f"  xauto={c.xauto}, yauto={c.yauto}")
assert c.xauto and c.yauto

print("\n=== 6. ホイールでカーソル中心の拡大 ===")
cv.render(doc, ax); canvas.draw()
px, py = ax.transData.transform((5.0, 0.0))
nav.on_scroll(MouseEvent("scroll_event", canvas, px, py, button="up"))
w = c.xmax - c.xmin
print(f"  拡大後 x=[{c.xmin:.3f}, {c.xmax:.3f}] 幅={w:.3f}")
print(f"  カーソル(x=5.0)が範囲内に留まる: {c.xmin < 5.0 < c.xmax}")
assert c.xmin < 5.0 < c.xmax

print("\n=== 7. 対数軸でのホイール拡大(負値にならないか) ===")
d2 = Document()
d2.series.append(Series(name="s", x=np.logspace(0,3,20), y=np.logspace(0,3,20)))
d2.config.xlog = d2.config.ylog = True
ax2 = plt.figure().add_subplot(111)
cv.render(d2, ax2); ax2.figure.canvas.draw()
nav2 = interaction.NavigationHandler(ax2.figure.canvas, ax2, get_doc=lambda: d2)
px, py = ax2.transData.transform((100.0, 100.0))
nav2.on_scroll(MouseEvent("scroll_event", ax2.figure.canvas, px, py, button="down"))
print(f"  縮小後 x=[{d2.config.xmin:.4g}, {d2.config.xmax:.4g}] 正のまま={d2.config.xmin > 0}")
assert d2.config.xmin > 0

print("\n=== 8. 注釈のドラッグ移動 ===")
c.xauto = c.yauto = True
artists = cv.render(doc, ax); canvas.draw(); nav.set_artists(artists)
ann = doc.annotations[0]
start = (ann.x, ann.y)
apx, apy = ax.transData.transform((ann.x, ann.y))
e = MouseEvent("button_press_event", canvas, apx, apy, MouseButton.LEFT)
nav.on_press(e)
print(f"  注釈をつかめた: {nav._drag_target is not None}")
assert nav._drag_target is not None
move(4.0, 0.5); release(4.0, 0.5)
print(f"  ({start[0]:.2f}, {start[1]:.2f}) -> ({ann.x:.2f}, {ann.y:.2f})")
assert (ann.x, ann.y) != start

print("\n=== 9. 空白部分のドラッグは注釈をつかまない ===")
artists = cv.render(doc, ax); canvas.draw(); nav.set_artists(artists)
press(9.5, -1.2)
grabbed = nav._drag_target is not None
release(9.6, -1.1)
print(f"  つかまなかった: {not grabbed}")
assert not grabbed

print("\n=== 10. 保存/読み込み (v2) と v1 ファイルの互換 ===")
d = json.loads(json.dumps(doc.to_dict(), ensure_ascii=False))
doc2 = Document.from_dict(d)
print(f"  往復: functions={len(doc2.functions)}, annotations={len(doc2.annotations)}, "
      f"注釈テキスト={doc2.annotations[1].text!r}")
assert len(doc2.functions) == 2 and len(doc2.annotations) == 2

v1 = {"version": 1, "config": {"xlabel": "t"},
      "series": [{"name": "old", "x": [1,2,3], "y": [1,4,9]}], "fits": []}
old = Document.from_dict(v1)
print(f"  v1ファイル読み込み: series={len(old.series)}, functions={len(old.functions)} (空)")
assert len(old.series) == 1 and old.functions == [] and old.annotations == []

print("\n=== 11. 最終描画 ===")
doc.config.xlabel = "%Ix%R / rad"
doc.config.ylabel = "%Iy%R"
cv.render(doc, ax)
fig.savefig("/tmp/demo2.png", dpi=150)
print("  demo2.png を出力")
print("\n全テスト通過")
