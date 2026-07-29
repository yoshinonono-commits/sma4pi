"""グラフ上のマウス操作。

左ドラッグ   : 範囲を四角で囲んで拡大 (注釈の上から始めた場合は注釈の移動)
右ドラッグ   : 平行移動
ホイール     : カーソル位置を中心に拡大縮小
ダブルクリック: 全体表示に戻す

拡大した結果は GraphConfig に書き戻すので、保存しても再描画しても保たれる。
"""

import numpy as np
from matplotlib.patches import Rectangle

MIN_DRAG_PX = 5   # これ未満のドラッグはクリック扱い
HIT_PAD_PX = 3    # 注釈の当たり判定を広げる量
ZOOM_STEP = 1.2


class NavigationHandler:
    def __init__(self, canvas, ax, get_doc, on_change=None, on_status=None):
        self.canvas = canvas
        self.ax = ax
        self.get_doc = get_doc
        self.on_change = on_change or (lambda: None)
        self.on_status = on_status or (lambda msg: None)

        self._artists = []          # [(annotation, artist)]
        self._rect = None
        self._press = None          # ズーム開始点 (データ座標)
        self._press_px = None
        self._pan = None            # 平行移動の開始状態
        self._drag_target = None    # 移動中の注釈
        self._background = None

        self._cids = [
            canvas.mpl_connect("button_press_event", self.on_press),
            canvas.mpl_connect("motion_notify_event", self.on_motion),
            canvas.mpl_connect("button_release_event", self.on_release),
            canvas.mpl_connect("scroll_event", self.on_scroll),
        ]

    def set_artists(self, artists):
        """再描画のたびに、最新の注釈 artist を渡してもらう。"""
        self._artists = artists or []

    def disconnect(self):
        for cid in self._cids:
            self.canvas.mpl_disconnect(cid)
        self._cids = []

    # --- 押した ----------------------------------------------------------

    def on_press(self, event):
        if event.inaxes is not self.ax:
            return

        if event.dblclick:
            self.reset_view()
            return

        if event.button == 1:
            hit = self._hit_annotation(event)
            if hit is not None:
                ann, artist = hit
                self._drag_target = (ann, artist, event.xdata, event.ydata)
                self.on_status(f"注釈「{ann.text}」を移動中")
                return
            self._press = (event.xdata, event.ydata)
            self._press_px = (event.x, event.y)
            self._rect = Rectangle(
                (event.xdata, event.ydata), 0, 0,
                fill=False, edgecolor="#3070c0", linestyle="--", linewidth=1.0,
            )
            self.ax.add_patch(self._rect)
            self._grab_background()

        elif event.button == 3:
            self._pan = (event.x, event.y,
                         self.ax.get_xlim(), self.ax.get_ylim())
            self.on_status("平行移動中 (右ドラッグ)")

    # --- 動かした --------------------------------------------------------

    def on_motion(self, event):
        if self._drag_target is not None:
            self._move_annotation(event)
            return
        if self._pan is not None:
            self._do_pan(event)
            return
        if self._rect is not None and self._press is not None:
            if event.xdata is None or event.ydata is None:
                return
            x0, y0 = self._press
            self._rect.set_bounds(
                min(x0, event.xdata), min(y0, event.ydata),
                abs(event.xdata - x0), abs(event.ydata - y0),
            )
            self._blit(self._rect)
            return
        # 何もしていないときは座標を出す
        if event.inaxes is self.ax and event.xdata is not None:
            self.on_status(f"x = {event.xdata:.6g}    y = {event.ydata:.6g}")

    # --- 離した ----------------------------------------------------------

    def on_release(self, event):
        if self._drag_target is not None:
            self._drag_target = None
            self._background = None
            self.on_change()
            self.on_status("")
            return

        if self._pan is not None:
            self._pan = None
            self._sync_limits()
            self.on_change()
            self.on_status("")
            return

        if self._rect is None:
            return

        rect, self._rect = self._rect, None
        press, self._press = self._press, None
        press_px, self._press_px = self._press_px, None
        self._background = None
        try:
            rect.remove()
        except (ValueError, NotImplementedError):
            pass

        if press is None or press_px is None or event.xdata is None:
            self.canvas.draw_idle()
            return

        # 動きが小さすぎるならクリックとみなして何もしない
        if (abs(event.x - press_px[0]) < MIN_DRAG_PX
                or abs(event.y - press_px[1]) < MIN_DRAG_PX):
            self.canvas.draw_idle()
            return

        x0, y0 = press
        xlo, xhi = sorted((x0, event.xdata))
        ylo, yhi = sorted((y0, event.ydata))

        cfg = self.get_doc().config
        cfg.xauto, cfg.xmin, cfg.xmax = False, float(xlo), float(xhi)
        cfg.yauto, cfg.ymin, cfg.ymax = False, float(ylo), float(yhi)
        self.on_change()
        self.on_status("拡大しました (ダブルクリックで全体表示)")

    # --- ホイール --------------------------------------------------------

    def on_scroll(self, event):
        if event.inaxes is not self.ax or event.xdata is None:
            return
        factor = 1 / ZOOM_STEP if event.button == "up" else ZOOM_STEP
        cfg = self.get_doc().config

        xlim = _scaled(self.ax.get_xlim(), event.xdata, factor, cfg.xlog)
        ylim = _scaled(self.ax.get_ylim(), event.ydata, factor, cfg.ylog)
        if xlim is None or ylim is None:
            return

        cfg.xauto, cfg.xmin, cfg.xmax = False, xlim[0], xlim[1]
        cfg.yauto, cfg.ymin, cfg.ymax = False, ylim[0], ylim[1]
        self.on_change()

    # --- 全体表示に戻す --------------------------------------------------

    def reset_view(self):
        cfg = self.get_doc().config
        cfg.xauto = True
        cfg.yauto = True
        self.on_change()
        self.on_status("全体表示に戻しました")

    # --- 内部 ------------------------------------------------------------

    def _hit_annotation(self, event):
        """カーソル下の注釈を探す。手前に描かれたものから順に判定する。

        artist.contains() は文字の外接矩形の縁でちょうど外れてしまうことがあるので、
        少し広げた矩形で当たり判定する。つかみそこねる方が困るため。
        """
        try:
            renderer = self.canvas.get_renderer()
        except AttributeError:
            renderer = None

        for ann, artist in reversed(self._artists):
            try:
                bbox = artist.get_window_extent(renderer)
            except Exception:
                continue
            if bbox.padded(HIT_PAD_PX).contains(event.x, event.y):
                return ann, artist
        return None

    def _move_annotation(self, event):
        if event.xdata is None or event.ydata is None:
            return
        ann, artist, px, py = self._drag_target

        if ann.coords == "data":
            ann.x += event.xdata - px
            ann.y += event.ydata - py
            self._drag_target = (ann, artist, event.xdata, event.ydata)
            artist.set_position((ann.x, ann.y))
        else:
            # 相対座標なら、ピクセル位置を軸内の割合に直す
            inv = self.ax.transAxes.inverted()
            fx, fy = inv.transform((event.x, event.y))
            ann.x, ann.y = float(fx), float(fy)
            artist.set_position((ann.x, ann.y))

        self._blit(artist)
        self.on_status(f"注釈の位置: ({ann.x:.4g}, {ann.y:.4g})")

    def _do_pan(self, event):
        if event.x is None:
            return
        x0px, y0px, xlim, ylim = self._pan
        inv = self.ax.transData.inverted()
        p0 = inv.transform((x0px, y0px))
        p1 = inv.transform((event.x, event.y))
        dx, dy = p0[0] - p1[0], p0[1] - p1[1]
        if not (np.isfinite(dx) and np.isfinite(dy)):
            return
        self.ax.set_xlim(xlim[0] + dx, xlim[1] + dx)
        self.ax.set_ylim(ylim[0] + dy, ylim[1] + dy)
        self.canvas.draw_idle()

    def _sync_limits(self):
        """ax の現在の表示範囲を config に書き戻す。"""
        cfg = self.get_doc().config
        xlim, ylim = self.ax.get_xlim(), self.ax.get_ylim()
        cfg.xauto, cfg.xmin, cfg.xmax = False, float(xlim[0]), float(xlim[1])
        cfg.yauto, cfg.ymin, cfg.ymax = False, float(ylim[0]), float(ylim[1])

    def _grab_background(self):
        try:
            self.canvas.draw()
            self._background = self.canvas.copy_from_bbox(self.ax.bbox)
        except Exception:
            self._background = None

    def _blit(self, artist):
        """背景を取れていれば blit で軽く、駄目なら普通に描き直す。"""
        if self._background is None:
            self.canvas.draw_idle()
            return
        try:
            self.canvas.restore_region(self._background)
            self.ax.draw_artist(artist)
            self.canvas.blit(self.ax.bbox)
        except Exception:
            self.canvas.draw_idle()


def _scaled(lim, center, factor, is_log):
    """center を動かさずに lim を factor 倍に広げる/狭める。"""
    lo, hi = lim
    if is_log:
        if lo <= 0 or hi <= 0 or center <= 0:
            return None
        lo, hi, center = np.log10(lo), np.log10(hi), np.log10(center)
    new_lo = center - (center - lo) * factor
    new_hi = center + (hi - center) * factor
    if not (np.isfinite(new_lo) and np.isfinite(new_hi)) or new_lo >= new_hi:
        return None
    if is_log:
        new_lo, new_hi = 10.0 ** new_lo, 10.0 ** new_hi
    return float(new_lo), float(new_hi)
