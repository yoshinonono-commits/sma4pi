"""Document を matplotlib の Axes に描画する処理と、Qt 埋め込み用キャンバス。"""

import numpy as np

from .notation import to_mathtext


_DASH = {"実線": "-", "破線": "--", "点線": ":", "一点鎖線": "-."}


def render(doc, ax):
    """Document の内容を ax に描き込み、注釈の artist リストを返す。

    戻り値は [(annotation, artist), ...]。ドラッグ移動の当たり判定に使う。
    """
    cfg = doc.config
    ax.clear()

    handles, labels = [], []

    for s in doc.series:
        if not s.visible:
            continue
        try:
            x, y = s.transformed()
        except Exception:
            continue
        if len(x) == 0:
            continue

        kw = s.mpl_kwargs()
        if s.yerr is not None and len(s.yerr) == len(y):
            container = ax.errorbar(x, y, yerr=s.yerr, capsize=3, **kw)
            line = container.lines[0]
        else:
            (line,) = ax.plot(x, y, **kw)
        if s.show_in_legend:
            handles.append(line)
            labels.append(to_mathtext(s.name) if _has_notation(s.name) else s.name)

    for f in doc.fits:
        if not f.visible:
            continue
        try:
            fx, fy = f.sample()
        except Exception:
            continue
        (line,) = ax.plot(
            fx, fy, color=f.color, linewidth=f.linewidth,
            linestyle=_DASH.get(f.linestyle, "-"),
        )
        if f.show_in_legend:
            handles.append(line)
            labels.append(f.name)

    # 任意関数の重ね書き。auto_range のときは実データの x 範囲に合わせる
    bounds = data_bounds(doc)
    for fn in doc.functions:
        if not fn.visible:
            continue
        try:
            fx, fy = fn.sample(fallback=bounds)
        except Exception:
            continue
        (line,) = ax.plot(
            fx, fy, color=fn.color, linewidth=fn.linewidth,
            linestyle=_DASH.get(fn.linestyle, "-"),
        )
        if fn.show_in_legend:
            handles.append(line)
            labels.append(to_mathtext(fn.name) if _has_notation(fn.name) else fn.name)

    if cfg.xlog:
        ax.set_xscale("log")
    if cfg.ylog:
        ax.set_yscale("log")

    if not cfg.xauto:
        ax.set_xlim(cfg.xmin, cfg.xmax)
    if not cfg.yauto:
        ax.set_ylim(cfg.ymin, cfg.ymax)

    ax.set_xlabel(to_mathtext(cfg.xlabel), fontsize=cfg.font_size)
    ax.set_ylabel(to_mathtext(cfg.ylabel), fontsize=cfg.font_size)
    if cfg.title:
        ax.set_title(to_mathtext(cfg.title), fontsize=cfg.font_size + 1)

    ax.tick_params(
        direction=cfg.tick_direction, top=True, right=True,
        which="both", labelsize=cfg.font_size - 1,
    )
    ax.grid(cfg.grid, alpha=0.3)

    if cfg.legend and handles:
        ax.legend(handles, labels, loc=cfg.legend_loc, fontsize=cfg.font_size - 1,
                  framealpha=0.9)

    # 注釈は最後に描く(常に手前に来るように)
    artists = []
    for a in doc.annotations:
        if not a.visible:
            continue
        artists.append((a, _draw_annotation(a, ax)))
    return artists


def _draw_annotation(a, ax):
    text = to_mathtext(a.text) if _has_notation(a.text) else a.text
    transform = ax.transAxes if a.coords == "axes" else ax.transData
    common = dict(
        color=a.color, fontsize=a.fontsize, ha=a.ha, va=a.va,
        rotation=a.rotation, clip_on=False, picker=True,
    )
    if a.arrow and a.coords == "data":
        return ax.annotate(
            text, xy=(a.ax_, a.ay_), xytext=(a.x, a.y),
            textcoords="data", xycoords="data",
            arrowprops=dict(arrowstyle="->", color=a.color, linewidth=1.0),
            **common,
        )
    return ax.text(a.x, a.y, text, transform=transform, **common)


def _has_notation(text):
    return "%" in text or "^" in text or "_" in text


def data_bounds(doc):
    """全系列の x 範囲を返す。データが無ければ None。"""
    xs = []
    for s in doc.series:
        if not s.visible:
            continue
        try:
            x, _ = s.transformed()
        except Exception:
            continue
        x = np.asarray(x, dtype=float)
        x = x[np.isfinite(x)]
        if len(x):
            xs.append((x.min(), x.max()))
    if not xs:
        return None
    return min(a for a, _ in xs), max(b for _, b in xs)


# --- Qt 埋め込み用 ---------------------------------------------------------

def make_canvas(parent=None):
    """FigureCanvas と Figure を作って返す。PySide6 が要る。"""
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure

    fig = Figure(figsize=(6, 4.5), dpi=100, layout="constrained")
    canvas = FigureCanvasQTAgg(fig)
    if parent is not None:
        canvas.setParent(parent)
    ax = fig.add_subplot(111)
    return canvas, fig, ax


def setup_japanese_font():
    """日本語ラベルが豆腐にならないよう、使えるフォントを探して設定する。"""
    import matplotlib
    from matplotlib import font_manager

    candidates = [
        "Yu Gothic", "Meiryo", "MS Gothic",           # Windows
        "Hiragino Sans", "Hiragino Kaku Gothic Pro",  # macOS
        "Noto Sans CJK JP", "IPAGothic", "TakaoGothic",  # Linux
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            matplotlib.rcParams["font.family"] = ["sans-serif"]
            matplotlib.rcParams["font.sans-serif"] = [name] + \
                matplotlib.rcParams["font.sans-serif"]
            break
    matplotlib.rcParams["axes.unicode_minus"] = False
    matplotlib.rcParams["mathtext.fontset"] = "cm"  # 論文らしい数式体裁
