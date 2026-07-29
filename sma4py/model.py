"""グラフの状態を保持するデータモデル。GUI からもファイル保存からも使う。"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional

import numpy as np

MARKERS = {
    "○ 白丸": "o", "● 黒丸": "o", "□ 四角": "s", "■ 黒四角": "s",
    "△ 三角": "^", "▲ 黒三角": "^", "◇ ひし形": "D", "× バツ": "x",
    "+ プラス": "+", "なし": "None",
}
FILLED = {"● 黒丸", "■ 黒四角", "▲ 黒三角"}

LINESTYLES = {"なし": "None", "実線": "-", "破線": "--", "点線": ":", "一点鎖線": "-."}


@dataclass
class Series:
    """1つのプロット系列。"""
    name: str = "series"
    x: np.ndarray = field(default_factory=lambda: np.array([]))
    y: np.ndarray = field(default_factory=lambda: np.array([]))
    yerr: Optional[np.ndarray] = None

    marker: str = "○ 白丸"
    linestyle: str = "なし"
    color: str = "#1f77b4"
    markersize: float = 6.0
    linewidth: float = 1.2
    visible: bool = True
    show_in_legend: bool = True

    # 数式変換 (空なら変換しない)
    x_expr: str = ""
    y_expr: str = ""

    source: str = ""

    def transformed(self):
        """数式変換を適用した (x, y) を返す。"""
        from . import expression

        x = np.asarray(self.x, dtype=float)
        y = np.asarray(self.y, dtype=float)
        if self.x_expr.strip():
            nx = expression.evaluate(self.x_expr, x, y)
            if nx is not None:
                x = nx
        if self.y_expr.strip():
            ny = expression.evaluate(self.y_expr, np.asarray(self.x, dtype=float), y)
            if ny is not None:
                y = ny
        return x, y

    def mpl_kwargs(self):
        marker = MARKERS.get(self.marker, "o")
        kw = {
            "marker": None if marker == "None" else marker,
            "linestyle": LINESTYLES.get(self.linestyle, "None"),
            "color": self.color,
            "markersize": self.markersize,
            "linewidth": self.linewidth,
        }
        if marker not in ("None", "x", "+"):
            if self.marker in FILLED:
                kw["markerfacecolor"] = self.color
            else:
                kw["markerfacecolor"] = "none"
            kw["markeredgecolor"] = self.color
            kw["markeredgewidth"] = 1.2
        return kw


@dataclass
class FitCurve:
    """フィッティング結果を曲線として保持する。"""
    name: str = "fit"
    expr: str = ""
    params: List[str] = field(default_factory=list)
    values: List[float] = field(default_factory=list)
    color: str = "#d62728"
    linewidth: float = 1.5
    linestyle: str = "実線"
    visible: bool = True
    show_in_legend: bool = True
    xmin: float = 0.0
    xmax: float = 1.0
    npoints: int = 400

    def sample(self):
        from .expression import make_function

        f = make_function(self.expr, self.params)
        x = np.linspace(self.xmin, self.xmax, self.npoints)
        with np.errstate(all="ignore"):
            y = np.asarray(f(x, *self.values), dtype=float)
        return x, y


@dataclass
class FunctionCurve:
    """データを持たない任意関数の重ね書き。 y = f(x) をそのまま描く。"""
    name: str = "f(x)"
    expr: str = "sin(x)"
    color: str = "#2ca02c"
    linewidth: float = 1.5
    linestyle: str = "実線"
    visible: bool = True
    show_in_legend: bool = True

    # auto_range が True なら、描画時に他系列の x 範囲へ自動で合わせる
    auto_range: bool = True
    xmin: float = 0.0
    xmax: float = 10.0
    npoints: int = 500

    def sample(self, fallback=None):
        """(x, y) を返す。auto_range のときは fallback=(min, max) を使う。"""
        from . import expression

        lo, hi = self.xmin, self.xmax
        if self.auto_range and fallback is not None:
            lo, hi = fallback
        if not np.isfinite(lo) or not np.isfinite(hi) or lo >= hi:
            lo, hi = 0.0, 10.0
        x = np.linspace(lo, hi, max(2, self.npoints))
        with np.errstate(all="ignore"):
            y = expression.evaluate(self.expr, x)
        if y is None:
            raise ValueError("式が空です。")
        return x, np.asarray(y, dtype=float)


@dataclass
class Annotation:
    """グラフ上に自由配置するテキスト注釈。"""
    text: str = "text"
    x: float = 0.5
    y: float = 0.5
    # "axes" は左下(0,0)〜右上(1,1)の相対座標、"data" はデータ座標
    coords: str = "axes"
    fontsize: float = 12.0
    color: str = "#000000"
    ha: str = "left"
    va: str = "center"
    rotation: float = 0.0
    visible: bool = True

    # 矢印(引き出し線)。使う場合は指し先をデータ座標で指定する
    arrow: bool = False
    ax_: float = 0.0
    ay_: float = 0.0


@dataclass
class GraphConfig:
    """軸やタイトルなど、グラフ全体の設定。"""
    title: str = ""
    xlabel: str = ""
    ylabel: str = ""

    xlog: bool = False
    ylog: bool = False

    xauto: bool = True
    yauto: bool = True
    xmin: float = 0.0
    xmax: float = 1.0
    ymin: float = 0.0
    ymax: float = 1.0

    legend: bool = False
    legend_loc: str = "best"
    grid: bool = False

    font_size: float = 12.0
    tick_direction: str = "in"
    width_inch: float = 6.0
    height_inch: float = 4.5


@dataclass
class Document:
    """1つのグラフ文書。"""
    config: GraphConfig = field(default_factory=GraphConfig)
    series: List[Series] = field(default_factory=list)
    fits: List[FitCurve] = field(default_factory=list)
    functions: List[FunctionCurve] = field(default_factory=list)
    annotations: List[Annotation] = field(default_factory=list)
    path: Optional[str] = None
    dirty: bool = False

    def to_dict(self):
        return {
            "version": 2,
            "config": asdict(self.config),
            "functions": [asdict(f) for f in self.functions],
            "annotations": [asdict(a) for a in self.annotations],
            "series": [
                {
                    **{k: v for k, v in asdict(s).items()
                       if k not in ("x", "y", "yerr")},
                    "x": np.asarray(s.x).tolist(),
                    "y": np.asarray(s.y).tolist(),
                    "yerr": None if s.yerr is None else np.asarray(s.yerr).tolist(),
                }
                for s in self.series
            ],
            "fits": [asdict(f) for f in self.fits],
        }

    @classmethod
    def from_dict(cls, d):
        doc = cls()
        doc.config = GraphConfig(**d.get("config", {}))
        for sd in d.get("series", []):
            sd = dict(sd)
            sd["x"] = np.array(sd.get("x", []), dtype=float)
            sd["y"] = np.array(sd.get("y", []), dtype=float)
            ye = sd.get("yerr")
            sd["yerr"] = None if ye is None else np.array(ye, dtype=float)
            doc.series.append(Series(**sd))
        for fd in d.get("fits", []):
            doc.fits.append(FitCurve(**fd))
        # version 1 のファイルには functions / annotations が無いので既定の空のまま
        for fd in d.get("functions", []):
            doc.functions.append(FunctionCurve(**fd))
        for ad in d.get("annotations", []):
            doc.annotations.append(Annotation(**ad))
        return doc


class History:
    """元に戻す/やり直すためのスナップショット管理。

    Document.to_dict() の結果をそのまま積むだけの単純な実装。GUI には依存しない。
    """

    def __init__(self, limit=50):
        self.limit = limit
        self._undo = []
        self._redo = []

    def clear(self):
        self._undo.clear()
        self._redo.clear()

    def can_undo(self):
        return bool(self._undo)

    def can_redo(self):
        return bool(self._redo)

    def push(self, snapshot):
        """変更を加える直前のスナップショットを積む。"""
        self._undo.append(snapshot)
        if len(self._undo) > self.limit:
            self._undo.pop(0)
        self._redo.clear()

    def undo(self, current):
        """current (今の状態) を redo 用に積み、直前のスナップショットを返す。"""
        if not self._undo:
            return None
        self._redo.append(current)
        return self._undo.pop()

    def redo(self, current):
        if not self._redo:
            return None
        self._undo.append(current)
        return self._redo.pop()
