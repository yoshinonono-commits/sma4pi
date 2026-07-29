"""メインウィンドウ。"""

import json
import os

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QSplitter,
    QVBoxLayout, QWidget,
)

from . import canvas as canvas_mod
from . import data_io
from .dialogs import (
    AnnotationDialog, AxisDialog, FitDialog, FunctionDialog, ImportDialog,
    SeriesDataDialog, SeriesDialog,
)
from .interaction import NavigationHandler
from .model import Annotation, Document, FitCurve, FunctionCurve, History

APP_NAME = "Sma4Py"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.doc = Document()
        self.history = History()
        self.setWindowTitle(APP_NAME)
        self.resize(1000, 680)

        canvas_mod.setup_japanese_font()
        self.canvas, self.fig, self.ax = canvas_mod.make_canvas(self)
        self.canvas.setFocusPolicy(Qt.StrongFocus)

        self.nav = NavigationHandler(
            self.canvas, self.ax,
            get_doc=lambda: self.doc,
            on_change=self._after_interaction,
            on_status=lambda msg: self.statusBar().showMessage(msg),
        )

        self._build_side_panel()
        self._build_menus()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.side)
        splitter.setStretchFactor(0, 1)
        splitter.setSizes([740, 260])
        self.setCentralWidget(splitter)

        self.statusBar().showMessage(
            "「データ」→「データファイルを開く」からテキストファイルを読み込んでください"
        )
        self.redraw()

    def _after_interaction(self):
        """マウス操作でグラフが変わったとき。拡大・平行移動は元に戻す対象にしない。"""
        self.doc.dirty = True
        self.redraw()

    # --- 元に戻す/やり直し --------------------------------------------------

    def _snapshot(self):
        """項目を変更する直前に呼び、その時点の状態を履歴に積む。"""
        self.history.push(self.doc.to_dict())
        self._sync_undo_actions()

    def _sync_undo_actions(self):
        self.undo_act.setEnabled(self.history.can_undo())
        self.redo_act.setEnabled(self.history.can_redo())

    def _restore(self, snapshot):
        path = self.doc.path
        self.doc = Document.from_dict(snapshot)
        self.doc.path = path
        self.doc.dirty = True
        self._sync_undo_actions()
        self.refresh_list()
        self.redraw()

    def undo(self):
        snapshot = self.history.undo(self.doc.to_dict())
        if snapshot is None:
            self.statusBar().showMessage("元に戻せる操作がありません", 3000)
            return
        self._restore(snapshot)

    def redo(self):
        snapshot = self.history.redo(self.doc.to_dict())
        if snapshot is None:
            self.statusBar().showMessage("やり直せる操作がありません", 3000)
            return
        self._restore(snapshot)

    # --- UI 組み立て ------------------------------------------------------

    def _build_side_panel(self):
        self.side = QWidget()
        layout = QVBoxLayout(self.side)
        layout.setContentsMargins(6, 6, 6, 6)

        layout.addWidget(QLabel("系列"))
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.itemChanged.connect(self._on_item_changed)
        self.list.itemDoubleClicked.connect(lambda _: self.edit_series())
        layout.addWidget(self.list, 1)

        row = QHBoxLayout()
        for text, slot in (("設定", self.edit_series), ("削除", self.remove_series),
                           ("データ点...", self.edit_series_data)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            row.addWidget(b)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        for text, slot in (("上へ", lambda: self._move(-1)),
                           ("下へ", lambda: self._move(1))):
            b = QPushButton(text)
            b.clicked.connect(slot)
            row2.addWidget(b)
        layout.addLayout(row2)
        return self.side

    def _build_menus(self):
        mb = self.menuBar()

        m = mb.addMenu("ファイル(&F)")
        self._act(m, "新規", self.new_doc, QKeySequence.New)
        self._act(m, "グラフを開く...", self.open_doc, QKeySequence.Open)
        self._act(m, "グラフを保存", self.save_doc, QKeySequence.Save)
        self._act(m, "名前を付けて保存...", self.save_doc_as, "Ctrl+Shift+S")
        m.addSeparator()
        self._act(m, "画像として書き出す...", self.export_image, "Ctrl+E")
        self._act(m, "印刷/PDF...", self.export_pdf, QKeySequence.Print)
        m.addSeparator()
        self._act(m, "終了", self.close, QKeySequence.Quit)

        m = mb.addMenu("編集(&E)")
        self.undo_act = self._act(m, "元に戻す", self.undo, QKeySequence.Undo)
        self.redo_act = self._act(m, "やり直す", self.redo, QKeySequence.Redo)
        self._sync_undo_actions()

        m = mb.addMenu("データ(&D)")
        self._act(m, "データファイルを開く...", self.import_data, "Ctrl+D")
        self._act(m, "系列の設定...", self.edit_series)
        self._act(m, "データ点を編集...", self.edit_series_data)
        self._act(m, "系列を削除", self.remove_series)

        m = mb.addMenu("グラフ(&G)")
        self._act(m, "グラフの設定...", self.edit_axes, "Ctrl+G")
        m.addSeparator()
        self._act(m, "X軸タイトル...", lambda: self.edit_axes("x"), "Ctrl+Shift+X")
        self._act(m, "Y軸タイトル...", lambda: self.edit_axes("y"), "Ctrl+Shift+Y")
        m.addSeparator()
        self._act(m, "凡例の表示/非表示", self.toggle_legend, "Ctrl+L")

        m = mb.addMenu("挿入(&I)")
        self._act(m, "任意関数の重ね書き...", self.add_function, "Ctrl+K")
        self._act(m, "テキスト注釈...", self.add_annotation, "Ctrl+T")

        m = mb.addMenu("表示(&V)")
        self._act(m, "全体を表示", self.reset_view, "Ctrl+0")
        self._act(m, "マウス操作について", self.show_mouse_help)

        m = mb.addMenu("解析(&A)")
        self._act(m, "最小二乗フィッティング...", self.run_fit, "Ctrl+F")
        self._act(m, "フィット曲線を全て消す", self.clear_fits)

        m = mb.addMenu("ヘルプ(&H)")
        self._act(m, "ラベル記法について", self.show_notation_help)
        self._act(m, f"{APP_NAME} について", self.show_about)

    def _act(self, menu, text, slot, shortcut=None):
        a = QAction(text, self)
        a.triggered.connect(slot)
        if shortcut:
            a.setShortcut(shortcut)
        menu.addAction(a)
        return a

    # --- 描画・同期 -------------------------------------------------------

    def redraw(self):
        artists = canvas_mod.render(self.doc, self.ax)
        self.nav.set_artists(artists)
        self.canvas.draw_idle()

    def _lists(self):
        """種類ごとのリストを返す。パネルの並び順と一致させる。"""
        return {
            "series": self.doc.series,
            "fit": self.doc.fits,
            "func": self.doc.functions,
            "ann": self.doc.annotations,
        }

    def refresh_list(self):
        self.list.blockSignals(True)
        current = self.list.currentRow()
        self.list.clear()
        for kind, prefix, items in (
            ("series", "", self.doc.series),
            ("fit", "  ↳ ", self.doc.fits),
            ("func", "ƒ ", self.doc.functions),
            ("ann", "T ", self.doc.annotations),
        ):
            for i, obj in enumerate(items):
                label = obj.text if kind == "ann" else obj.name
                it = QListWidgetItem(prefix + label)
                it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
                it.setCheckState(Qt.Checked if obj.visible else Qt.Unchecked)
                it.setData(Qt.UserRole, (kind, i))
                if kind != "series":
                    it.setForeground(Qt.darkGray)
                self.list.addItem(it)
        self.list.blockSignals(False)
        if 0 <= current < self.list.count():
            self.list.setCurrentRow(current)

    def _ref(self, row=None):
        """選択中の項目を (kind, index, オブジェクト) で返す。無ければ None。"""
        row = self.list.currentRow() if row is None else row
        item = self.list.item(row)
        if item is None:
            return None
        kind, i = item.data(Qt.UserRole)
        items = self._lists()[kind]
        if not (0 <= i < len(items)):
            return None
        return kind, i, items[i]

    def _on_item_changed(self, item):
        ref = self._ref(self.list.row(item))
        if ref is None:
            return
        self._snapshot()
        ref[2].visible = item.checkState() == Qt.Checked
        self.doc.dirty = True
        self.redraw()

    def _current_series_index(self):
        ref = self._ref()
        return ref[1] if ref and ref[0] == "series" else -1

    def _move(self, delta):
        """同じ種類の中でだけ並べ替える。"""
        ref = self._ref()
        if ref is None:
            return
        kind, i, _ = ref
        items = self._lists()[kind]
        j = i + delta
        if not (0 <= j < len(items)):
            return
        self._snapshot()
        items[i], items[j] = items[j], items[i]
        self.doc.dirty = True
        self.refresh_list()
        # 動かした項目を選び直す
        for row in range(self.list.count()):
            if self.list.item(row).data(Qt.UserRole) == (kind, j):
                self.list.setCurrentRow(row)
                break
        self.redraw()

    # --- ファイル ---------------------------------------------------------

    def import_data(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "データファイルを開く", "",
            "データファイル (*.txt *.dat *.csv *.tsv);;すべてのファイル (*)",
        )
        if not path:
            return
        try:
            data, header = data_io.load_table(path)
        except Exception as e:
            QMessageBox.critical(self, "読み込みエラー", str(e))
            return

        dlg = ImportDialog(data, header, os.path.basename(path), self)
        if dlg.exec() != ImportDialog.Accepted:
            return
        s = dlg.series()
        s.source = path
        self._snapshot()
        self.doc.series.append(s)
        self.doc.dirty = True
        self.refresh_list()
        self.redraw()
        self.statusBar().showMessage(f"{s.name}: {len(s.x)} 点を読み込みました", 5000)

    def new_doc(self):
        if not self._confirm_discard():
            return
        self.doc = Document()
        self.history.clear()
        self._sync_undo_actions()
        self.refresh_list()
        self.redraw()
        self.setWindowTitle(APP_NAME)

    def open_doc(self):
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "グラフを開く", "", "Sma4Py グラフ (*.s4p);;すべてのファイル (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.doc = Document.from_dict(json.load(f))
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"開けませんでした: {e}")
            return
        self.doc.path = path
        self.history.clear()
        self._sync_undo_actions()
        self.refresh_list()
        self.redraw()
        self.setWindowTitle(f"{APP_NAME} - {os.path.basename(path)}")

    def save_doc(self):
        if not self.doc.path:
            return self.save_doc_as()
        return self._write(self.doc.path)

    def save_doc_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "名前を付けて保存", "", "Sma4Py グラフ (*.s4p)")
        if not path:
            return False
        if not path.lower().endswith(".s4p"):
            path += ".s4p"
        return self._write(path)

    def _write(self, path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.doc.to_dict(), f, ensure_ascii=False, indent=1)
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存できませんでした: {e}")
            return False
        self.doc.path = path
        self.doc.dirty = False
        self.setWindowTitle(f"{APP_NAME} - {os.path.basename(path)}")
        self.statusBar().showMessage("保存しました", 3000)
        return True

    def _confirm_discard(self):
        if not self.doc.dirty:
            return True
        r = QMessageBox.question(
            self, "確認", "保存していない変更があります。保存しますか？",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
        )
        if r == QMessageBox.Cancel:
            return False
        if r == QMessageBox.Save:
            return self.save_doc()
        return True

    def closeEvent(self, event):
        event.accept() if self._confirm_discard() else event.ignore()

    def export_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "画像として書き出す", "",
            "PNG (*.png);;PDF (*.pdf);;SVG (*.svg);;EPS (*.eps)",
        )
        if not path:
            return
        try:
            self.fig.savefig(path, dpi=300)
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"書き出せませんでした: {e}")
            return
        self.statusBar().showMessage(f"{os.path.basename(path)} に保存しました", 4000)

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "PDF に出力", "", "PDF (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        self.fig.savefig(path)
        self.statusBar().showMessage(f"{os.path.basename(path)} に出力しました", 4000)

    # --- 編集 -------------------------------------------------------------

    def edit_axes(self, focus=None):
        dlg = AxisDialog(self.doc.config, self)
        if focus == "x":
            dlg.xlabel_edit.edit.setFocus()
        elif focus == "y":
            dlg.ylabel_edit.edit.setFocus()
        if dlg.exec() == AxisDialog.Accepted:
            self._snapshot()
            dlg.apply_to(self.doc.config)
            self.doc.dirty = True
            self.redraw()

    def edit_series(self):
        """選択中の項目を、その種類に合ったダイアログで編集する。"""
        ref = self._ref()
        if ref is None:
            QMessageBox.information(self, APP_NAME, "項目を選んでください。")
            return
        kind, _, obj = ref

        if kind == "series":
            dlg = SeriesDialog(obj, self)
        elif kind == "func":
            dlg = FunctionDialog(obj, self)
        elif kind == "ann":
            dlg = AnnotationDialog(obj, self)
        else:
            QMessageBox.information(
                self, APP_NAME,
                "フィット曲線は編集できません。\n"
                "式やパラメータを変えるには、もう一度フィットを実行してください。")
            return

        if dlg.exec() == QDialog.Accepted:
            self._snapshot()
            dlg.apply_to(obj)
            self.doc.dirty = True
            self.refresh_list()
            self.redraw()

    def edit_series_data(self):
        """選択中の系列のデータ点を表形式で編集する。"""
        ref = self._ref()
        if ref is None or ref[0] != "series":
            QMessageBox.information(self, APP_NAME, "系列を選んでください。")
            return
        _, _, s = ref
        dlg = SeriesDataDialog(s, self)
        if dlg.exec() != QDialog.Accepted:
            return
        self._snapshot()
        dlg.apply_to(s)
        self.doc.dirty = True
        self.refresh_list()
        self.redraw()

    def remove_series(self):
        ref = self._ref()
        if ref is None:
            return
        kind, i, _ = ref
        self._snapshot()
        del self._lists()[kind][i]
        self.doc.dirty = True
        self.refresh_list()
        self.redraw()

    def add_function(self):
        f = FunctionCurve()
        # データがあれば、その x 範囲を既定値にしておく
        bounds = canvas_mod.data_bounds(self.doc)
        if bounds:
            f.xmin, f.xmax = bounds
        dlg = FunctionDialog(f, self)
        if dlg.exec() != QDialog.Accepted:
            return
        dlg.apply_to(f)
        self._snapshot()
        self.doc.functions.append(f)
        self.doc.dirty = True
        self.refresh_list()
        self.redraw()

    def add_annotation(self):
        a = Annotation(text="ここに文字", x=0.5, y=0.9, coords="axes", ha="center")
        a.fontsize = self.doc.config.font_size
        dlg = AnnotationDialog(a, self)
        if dlg.exec() != QDialog.Accepted:
            return
        dlg.apply_to(a)
        self._snapshot()
        self.doc.annotations.append(a)
        self.doc.dirty = True
        self.refresh_list()
        self.redraw()
        self.statusBar().showMessage(
            "グラフ上で文字をドラッグすると位置を動かせます", 6000)

    def reset_view(self):
        self.nav.reset_view()

    def toggle_legend(self):
        self._snapshot()
        self.doc.config.legend = not self.doc.config.legend
        self.doc.dirty = True
        self.redraw()

    # --- 解析 -------------------------------------------------------------

    def run_fit(self):
        if not self.doc.series:
            QMessageBox.information(self, APP_NAME, "先にデータを読み込んでください。")
            return
        dlg = FitDialog(self.doc.series, self)
        if dlg.exec() != FitDialog.Accepted or dlg.result is None:
            return
        res, s = dlg.result
        x, _ = s.transformed()
        x = np.asarray(x, dtype=float)
        x = x[np.isfinite(x)]
        self._snapshot()
        self.doc.fits.append(FitCurve(
            name=f"fit: {s.name}",
            expr=res.expr, params=res.params, values=res.values,
            xmin=float(x.min()), xmax=float(x.max()),
        ))
        self.doc.dirty = True
        self.refresh_list()
        self.redraw()

    def clear_fits(self):
        self._snapshot()
        self.doc.fits.clear()
        self.doc.dirty = True
        self.refresh_list()
        self.redraw()

    # --- ヘルプ -----------------------------------------------------------

    def show_mouse_help(self):
        QMessageBox.information(
            self, "マウス操作",
            "左ドラッグ\t囲んだ範囲を拡大\n"
            "右ドラッグ\t平行移動\n"
            "ホイール\tカーソル位置を中心に拡大縮小\n"
            "ダブルクリック\t全体表示に戻す\n\n"
            "注釈の文字を左ドラッグすると、その注釈を動かせます。",
        )

    def show_notation_help(self):
        from .dialogs import NOTATION_HELP
        QMessageBox.information(self, "ラベル記法", NOTATION_HELP)

    def show_about(self):
        QMessageBox.about(
            self, f"{APP_NAME} について",
            f"<b>{APP_NAME}</b><br><br>"
            "散布図の作図と最小二乗フィッティングのためのツールです。<br>"
            "Python + PySide6 + Matplotlib + SciPy<br><br>"
            "Sma4Win の操作感を参考にした独立実装で、"
            "元ソフトのコードは含みません。",
        )
