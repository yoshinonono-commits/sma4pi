"""各種ダイアログ。"""

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from . import fitting
from .model import LINESTYLES, MARKERS, Series
from .notation import to_mathtext


class ColorButton(QPushButton):
    """押すと色選択ダイアログが出るボタン。"""

    def __init__(self, color="#1f77b4", parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedWidth(60)
        self.clicked.connect(self._pick)
        self._refresh()

    def _refresh(self):
        self.setStyleSheet(
            f"background-color: {self._color}; border: 1px solid #888;")
        self.setText("")

    def _pick(self):
        c = QColorDialog.getColor(QColor(self._color), self, "色を選ぶ")
        if c.isValid():
            self._color = c.name()
            self._refresh()

    def color(self):
        return self._color

    def setColor(self, c):
        self._color = c
        self._refresh()


class ImportDialog(QDialog):
    """データファイルを開いたあとの列選択。Sma4Win の「データファイルを開く」相当。"""

    def __init__(self, data, header, filename, parent=None):
        super().__init__(parent)
        self.setWindowTitle("列の選択")
        self.data = data
        self.header = header
        self.resize(560, 460)

        ncol = data.shape[1]
        items = [f"{i + 1}: {header[i]}" for i in range(ncol)]

        self.x_combo = QComboBox()
        self.x_combo.addItems(items)
        self.y_combo = QComboBox()
        self.y_combo.addItems(items)
        self.y_combo.setCurrentIndex(min(1, ncol - 1))

        self.err_combo = QComboBox()
        self.err_combo.addItem("なし")
        self.err_combo.addItems(items)

        self.name_edit = QLineEdit(filename)

        self.marker_combo = QComboBox()
        self.marker_combo.addItems(list(MARKERS))
        self.line_combo = QComboBox()
        self.line_combo.addItems(list(LINESTYLES))
        self.color_btn = ColorButton()

        form = QFormLayout()
        form.addRow("X 軸にとる列", self.x_combo)
        form.addRow("Y 軸にとる列", self.y_combo)
        form.addRow("Y 誤差の列", self.err_combo)
        form.addRow("系列名", self.name_edit)
        form.addRow("マーカー", self.marker_combo)
        form.addRow("線", self.line_combo)
        form.addRow("色", self.color_btn)

        # データのプレビュー
        preview = QTableWidget()
        nrow = min(len(data), 100)
        preview.setRowCount(nrow)
        preview.setColumnCount(ncol)
        preview.setHorizontalHeaderLabels(header)
        for r in range(nrow):
            for c in range(ncol):
                v = data[r, c]
                txt = "" if not np.isfinite(v) else f"{v:g}"
                preview.setItem(r, c, QTableWidgetItem(txt))
        preview.setEditTriggers(QTableWidget.NoEditTriggers)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(QLabel(f"プレビュー (先頭 {nrow} 行 / 全 {len(data)} 行)"))
        layout.addWidget(preview, 1)
        layout.addWidget(buttons)

    def series(self):
        xi = self.x_combo.currentIndex()
        yi = self.y_combo.currentIndex()
        ei = self.err_combo.currentIndex()
        yerr = None if ei == 0 else self.data[:, ei - 1]
        return Series(
            name=self.name_edit.text() or "series",
            x=self.data[:, xi].copy(),
            y=self.data[:, yi].copy(),
            yerr=None if yerr is None else yerr.copy(),
            marker=self.marker_combo.currentText(),
            linestyle=self.line_combo.currentText(),
            color=self.color_btn.color(),
        )


class LabelEdit(QWidget):
    """Sma4 記法の入力欄。変換結果をその場でプレビューする。"""

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.edit = QLineEdit(text)
        self.preview = QLabel()
        self.preview.setStyleSheet("color: #666; font-size: 11px;")
        self.edit.textChanged.connect(self._update)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.edit)
        layout.addWidget(self.preview)
        self._update()

    def _update(self):
        self.preview.setText("→ " + (to_mathtext(self.edit.text()) or "(空)"))

    def text(self):
        return self.edit.text()


NOTATION_HELP = (
    "記法:  %I イタリック / %R 立体 / %G ギリシャ文字 / %A ギリシャ解除\n"
    "        ^ 上付き / _ 下付き / @ 上付き下付き解除\n"
    "例:  %II%R / A     →  I / A （I だけ斜体）\n"
    "      %I%Gl%A%R / nm →  λ / nm\n"
    "      N / m^2@      →  N / m²"
)


class AxisDialog(QDialog):
    """軸・タイトル・凡例などの設定。"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("グラフの設定")
        self.cfg = config
        self.resize(480, 620)

        self.title_edit = LabelEdit(config.title)
        self.xlabel_edit = LabelEdit(config.xlabel)
        self.ylabel_edit = LabelEdit(config.ylabel)

        labels = QGroupBox("タイトル・軸ラベル")
        lf = QFormLayout(labels)
        lf.addRow("グラフタイトル", self.title_edit)
        lf.addRow("X 軸タイトル", self.xlabel_edit)
        lf.addRow("Y 軸タイトル", self.ylabel_edit)
        help_label = QLabel(NOTATION_HELP)
        help_label.setStyleSheet("color: #555; font-size: 11px;")
        lf.addRow(help_label)

        # X 軸
        self.xauto = QCheckBox("自動")
        self.xauto.setChecked(config.xauto)
        self.xmin = QDoubleSpinBox()
        self.xmax = QDoubleSpinBox()
        self.xlog = QCheckBox("対数軸")
        self.xlog.setChecked(config.xlog)
        xbox = self._range_box("X 軸", self.xauto, self.xmin, self.xmax,
                               self.xlog, config.xmin, config.xmax)

        self.yauto = QCheckBox("自動")
        self.yauto.setChecked(config.yauto)
        self.ymin = QDoubleSpinBox()
        self.ymax = QDoubleSpinBox()
        self.ylog = QCheckBox("対数軸")
        self.ylog.setChecked(config.ylog)
        ybox = self._range_box("Y 軸", self.yauto, self.ymin, self.ymax,
                               self.ylog, config.ymin, config.ymax)

        # 見た目
        self.legend = QCheckBox("凡例を表示")
        self.legend.setChecked(config.legend)
        self.legend_loc = QComboBox()
        self.legend_loc.addItems([
            "best", "upper right", "upper left", "lower left", "lower right",
            "center right", "center left",
        ])
        self.legend_loc.setCurrentText(config.legend_loc)
        self.grid = QCheckBox("グリッド線を表示")
        self.grid.setChecked(config.grid)
        self.font_size = QDoubleSpinBox()
        self.font_size.setRange(4, 40)
        self.font_size.setValue(config.font_size)
        self.tick_dir = QComboBox()
        self.tick_dir.addItems(["in", "out"])
        self.tick_dir.setCurrentText(config.tick_direction)

        look = QGroupBox("体裁")
        lkf = QFormLayout(look)
        lkf.addRow(self.legend)
        lkf.addRow("凡例の位置", self.legend_loc)
        lkf.addRow(self.grid)
        lkf.addRow("文字サイズ", self.font_size)
        lkf.addRow("目盛りの向き", self.tick_dir)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(labels)
        layout.addWidget(xbox)
        layout.addWidget(ybox)
        layout.addWidget(look)
        layout.addStretch(1)
        layout.addWidget(buttons)

    def _range_box(self, title, auto, vmin, vmax, log, cur_min, cur_max):
        box = QGroupBox(title)
        for sb, val in ((vmin, cur_min), (vmax, cur_max)):
            sb.setRange(-1e12, 1e12)
            sb.setDecimals(6)
            sb.setValue(val)
        grid = QGridLayout(box)
        grid.addWidget(auto, 0, 0)
        grid.addWidget(log, 0, 1)
        grid.addWidget(QLabel("最小"), 1, 0)
        grid.addWidget(vmin, 1, 1)
        grid.addWidget(QLabel("最大"), 2, 0)
        grid.addWidget(vmax, 2, 1)

        def sync():
            vmin.setEnabled(not auto.isChecked())
            vmax.setEnabled(not auto.isChecked())

        auto.toggled.connect(sync)
        sync()
        return box

    def apply_to(self, cfg):
        cfg.title = self.title_edit.text()
        cfg.xlabel = self.xlabel_edit.text()
        cfg.ylabel = self.ylabel_edit.text()
        cfg.xauto = self.xauto.isChecked()
        cfg.xmin, cfg.xmax = self.xmin.value(), self.xmax.value()
        cfg.xlog = self.xlog.isChecked()
        cfg.yauto = self.yauto.isChecked()
        cfg.ymin, cfg.ymax = self.ymin.value(), self.ymax.value()
        cfg.ylog = self.ylog.isChecked()
        cfg.legend = self.legend.isChecked()
        cfg.legend_loc = self.legend_loc.currentText()
        cfg.grid = self.grid.isChecked()
        cfg.font_size = self.font_size.value()
        cfg.tick_direction = self.tick_dir.currentText()


class SeriesDialog(QDialog):
    """系列ごとのプロット属性と数式変換。"""

    def __init__(self, series, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系列の設定")
        self.s = series
        self.resize(430, 400)

        self.name = QLineEdit(series.name)
        self.marker = QComboBox()
        self.marker.addItems(list(MARKERS))
        self.marker.setCurrentText(series.marker)
        self.line = QComboBox()
        self.line.addItems(list(LINESTYLES))
        self.line.setCurrentText(series.linestyle)
        self.color = ColorButton(series.color)
        self.msize = QDoubleSpinBox()
        self.msize.setRange(0, 40)
        self.msize.setValue(series.markersize)
        self.lwidth = QDoubleSpinBox()
        self.lwidth.setRange(0, 20)
        self.lwidth.setValue(series.linewidth)
        self.in_legend = QCheckBox("凡例に載せる")
        self.in_legend.setChecked(series.show_in_legend)

        look = QGroupBox("プロット")
        lf = QFormLayout(look)
        lf.addRow("系列名", self.name)
        lf.addRow("マーカー", self.marker)
        lf.addRow("マーカーサイズ", self.msize)
        lf.addRow("線", self.line)
        lf.addRow("線幅", self.lwidth)
        lf.addRow("色", self.color)
        lf.addRow(self.in_legend)

        self.x_expr = QLineEdit(series.x_expr)
        self.x_expr.setPlaceholderText("例: x*3  (空欄なら変換しない)")
        self.y_expr = QLineEdit(series.y_expr)
        self.y_expr.setPlaceholderText("例: log10(y)  や  diff(y)")

        conv = QGroupBox("数式変換")
        cf = QFormLayout(conv)
        cf.addRow("X 値変換", self.x_expr)
        cf.addRow("Y 値変換", self.y_expr)
        hint = QLabel(
            "使える名前: x, y, i(点番号), pi, e\n"
            "関数: sin cos tan exp log log10 sqrt abs diff() integ() など"
        )
        hint.setStyleSheet("color: #555; font-size: 11px;")
        cf.addRow(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._check_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(look)
        layout.addWidget(conv)
        layout.addStretch(1)
        layout.addWidget(buttons)

    def _check_and_accept(self):
        """OK を押した時点で式を試し、壊れていれば閉じずに知らせる。"""
        from . import expression

        for label, expr in (("X 値変換", self.x_expr.text()),
                            ("Y 値変換", self.y_expr.text())):
            if not expr.strip():
                continue
            try:
                expression.evaluate(expr, self.s.x, self.s.y)
            except Exception as e:
                QMessageBox.warning(self, "式のエラー", f"{label}: {e}")
                return
        self.accept()

    def apply_to(self, s):
        s.name = self.name.text()
        s.marker = self.marker.currentText()
        s.linestyle = self.line.currentText()
        s.color = self.color.color()
        s.markersize = self.msize.value()
        s.linewidth = self.lwidth.value()
        s.show_in_legend = self.in_legend.isChecked()
        s.x_expr = self.x_expr.text()
        s.y_expr = self.y_expr.text()


class FunctionDialog(QDialog):
    """データを持たない任意関数の重ね書き。"""

    def __init__(self, func, parent=None):
        super().__init__(parent)
        self.setWindowTitle("任意関数の重ね書き")
        self.f = func
        self.resize(430, 400)

        self.name = QLineEdit(func.name)
        self.expr = QLineEdit(func.expr)
        self.expr.setPlaceholderText("例: 2*sin(x)/x")

        model_box = QGroupBox("関数")
        mf = QFormLayout(model_box)
        mf.addRow("名前", self.name)
        mf.addRow("y =", self.expr)
        hint = QLabel(
            "x を変数とする式を書きます。\n"
            "関数: sin cos tan exp log log10 sqrt abs erf jn yn / 定数: pi, e"
        )
        hint.setStyleSheet("color: #555; font-size: 11px;")
        mf.addRow(hint)

        self.auto = QCheckBox("描画範囲をデータに合わせる")
        self.auto.setChecked(func.auto_range)
        self.xmin = QDoubleSpinBox()
        self.xmax = QDoubleSpinBox()
        for sb, v in ((self.xmin, func.xmin), (self.xmax, func.xmax)):
            sb.setRange(-1e12, 1e12)
            sb.setDecimals(6)
            sb.setValue(v)
        self.npoints = QSpinBox()
        self.npoints.setRange(2, 100000)
        self.npoints.setValue(func.npoints)

        range_box = QGroupBox("描画範囲")
        rf = QFormLayout(range_box)
        rf.addRow(self.auto)
        rf.addRow("x 最小", self.xmin)
        rf.addRow("x 最大", self.xmax)
        rf.addRow("分割数", self.npoints)

        def sync():
            self.xmin.setEnabled(not self.auto.isChecked())
            self.xmax.setEnabled(not self.auto.isChecked())

        self.auto.toggled.connect(sync)
        sync()

        self.color = ColorButton(func.color)
        self.line = QComboBox()
        self.line.addItems([k for k in LINESTYLES if k != "なし"])
        self.line.setCurrentText(func.linestyle)
        self.lwidth = QDoubleSpinBox()
        self.lwidth.setRange(0.1, 20)
        self.lwidth.setValue(func.linewidth)
        self.in_legend = QCheckBox("凡例に載せる")
        self.in_legend.setChecked(func.show_in_legend)

        look = QGroupBox("線")
        lf = QFormLayout(look)
        lf.addRow("色", self.color)
        lf.addRow("線種", self.line)
        lf.addRow("線幅", self.lwidth)
        lf.addRow(self.in_legend)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._check_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(model_box)
        layout.addWidget(range_box)
        layout.addWidget(look)
        layout.addStretch(1)
        layout.addWidget(buttons)

    def _check_and_accept(self):
        from . import expression

        try:
            probe = np.linspace(self.xmin.value(), self.xmax.value(), 5)
            with np.errstate(all="ignore"):
                r = expression.evaluate(self.expr.text(), probe)
            if r is None:
                raise ValueError("式が空です。")
        except Exception as e:
            QMessageBox.warning(self, "式のエラー", str(e))
            return
        self.accept()

    def apply_to(self, f):
        f.name = self.name.text() or "f(x)"
        f.expr = self.expr.text()
        f.auto_range = self.auto.isChecked()
        f.xmin, f.xmax = self.xmin.value(), self.xmax.value()
        f.npoints = self.npoints.value()
        f.color = self.color.color()
        f.linestyle = self.line.currentText()
        f.linewidth = self.lwidth.value()
        f.show_in_legend = self.in_legend.isChecked()


class AnnotationDialog(QDialog):
    """テキスト注釈の設定。位置はグラフ上のドラッグでも動かせる。"""

    def __init__(self, ann, parent=None):
        super().__init__(parent)
        self.setWindowTitle("テキスト注釈")
        self.a = ann
        self.resize(430, 440)

        self.text = LabelEdit(ann.text)

        self.coords = QComboBox()
        self.coords.addItem("グラフ枠に対する相対位置 (0〜1)", "axes")
        self.coords.addItem("データ座標", "data")
        self.coords.setCurrentIndex(0 if ann.coords == "axes" else 1)

        self.x = QDoubleSpinBox()
        self.y = QDoubleSpinBox()
        for sb, v in ((self.x, ann.x), (self.y, ann.y)):
            sb.setRange(-1e12, 1e12)
            sb.setDecimals(6)
            sb.setValue(v)

        pos = QGroupBox("位置")
        pf = QFormLayout(pos)
        pf.addRow("文字", self.text)
        pf.addRow("座標系", self.coords)
        pf.addRow("x", self.x)
        pf.addRow("y", self.y)
        tip = QLabel("グラフ上で文字をドラッグしても動かせます。")
        tip.setStyleSheet("color: #555; font-size: 11px;")
        pf.addRow(tip)

        self.arrow = QCheckBox("引き出し線を付ける (データ座標のときのみ)")
        self.arrow.setChecked(ann.arrow)
        self.ax_ = QDoubleSpinBox()
        self.ay_ = QDoubleSpinBox()
        for sb, v in ((self.ax_, ann.ax_), (self.ay_, ann.ay_)):
            sb.setRange(-1e12, 1e12)
            sb.setDecimals(6)
            sb.setValue(v)

        arr = QGroupBox("引き出し線")
        af = QFormLayout(arr)
        af.addRow(self.arrow)
        af.addRow("指し先 x", self.ax_)
        af.addRow("指し先 y", self.ay_)

        self.fontsize = QDoubleSpinBox()
        self.fontsize.setRange(4, 72)
        self.fontsize.setValue(ann.fontsize)
        self.color = ColorButton(ann.color)
        self.ha = QComboBox()
        self.ha.addItems(["left", "center", "right"])
        self.ha.setCurrentText(ann.ha)
        self.va = QComboBox()
        self.va.addItems(["top", "center", "bottom", "baseline"])
        self.va.setCurrentText(ann.va)
        self.rotation = QDoubleSpinBox()
        self.rotation.setRange(-360, 360)
        self.rotation.setValue(ann.rotation)

        look = QGroupBox("体裁")
        lf = QFormLayout(look)
        lf.addRow("文字サイズ", self.fontsize)
        lf.addRow("色", self.color)
        lf.addRow("横揃え", self.ha)
        lf.addRow("縦揃え", self.va)
        lf.addRow("回転 (度)", self.rotation)

        def sync():
            data_mode = self.coords.currentData() == "data"
            self.arrow.setEnabled(data_mode)
            on = data_mode and self.arrow.isChecked()
            self.ax_.setEnabled(on)
            self.ay_.setEnabled(on)

        self.coords.currentIndexChanged.connect(sync)
        self.arrow.toggled.connect(sync)
        sync()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(pos)
        layout.addWidget(arr)
        layout.addWidget(look)
        layout.addStretch(1)
        layout.addWidget(buttons)

    def apply_to(self, a):
        a.text = self.text.text()
        a.coords = self.coords.currentData()
        a.x, a.y = self.x.value(), self.y.value()
        a.arrow = self.arrow.isChecked() and a.coords == "data"
        a.ax_, a.ay_ = self.ax_.value(), self.ay_.value()
        a.fontsize = self.fontsize.value()
        a.color = self.color.color()
        a.ha = self.ha.currentText()
        a.va = self.va.currentText()
        a.rotation = self.rotation.value()


class FitDialog(QDialog):
    """最小二乗フィッティング。Sma4Win の a=, b=, c= 入力欄に相当する。"""

    def __init__(self, series, parent=None):
        super().__init__(parent)
        self.setWindowTitle("最小二乗フィッティング")
        self.series_list = series
        self.result = None
        self.resize(520, 560)

        self.target = QComboBox()
        self.target.addItems([s.name for s in series])

        self.preset = QComboBox()
        self.preset.addItem("(自分で式を書く)")
        self.preset.addItems([p[0] for p in fitting.PRESETS])
        self.preset.currentIndexChanged.connect(self._apply_preset)

        self.expr = QLineEdit("a + b*x")
        self.params = QLineEdit("a, b")
        self.params.textChanged.connect(self._rebuild_p0)

        top = QGroupBox("モデル")
        tf = QFormLayout(top)
        tf.addRow("対象の系列", self.target)
        tf.addRow("よく使う式", self.preset)
        tf.addRow("y =", self.expr)
        tf.addRow("パラメータ", self.params)

        self.p0_box = QGroupBox("初期値")
        self.p0_layout = QFormLayout(self.p0_box)
        self.p0_widgets = {}

        self.use_err = QCheckBox("Y 誤差を重みに使う (誤差列がある場合)")

        self.run_btn = QPushButton("フィット実行")
        self.run_btn.clicked.connect(self._run)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("結果がここに出ます")

        buttons = QDialogButtonBox()
        self.add_btn = buttons.addButton("グラフに追加", QDialogButtonBox.AcceptRole)
        self.add_btn.setEnabled(False)
        buttons.addButton("閉じる", QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(top)
        layout.addWidget(self.p0_box)
        layout.addWidget(self.use_err)
        layout.addWidget(self.run_btn)
        layout.addWidget(self.output, 1)
        layout.addWidget(buttons)

        self._rebuild_p0()

    def _apply_preset(self, idx):
        if idx <= 0:
            return
        _, expr, params = fitting.PRESETS[idx - 1]
        self.expr.setText(expr)
        self.params.setText(", ".join(params))

    def _param_names(self):
        return [p.strip() for p in self.params.text().split(",") if p.strip()]

    def _rebuild_p0(self):
        names = self._param_names()
        old = {k: w.value() for k, w in self.p0_widgets.items()}
        while self.p0_layout.rowCount():
            self.p0_layout.removeRow(0)
        self.p0_widgets = {}
        for name in names:
            sb = QDoubleSpinBox()
            sb.setRange(-1e12, 1e12)
            sb.setDecimals(6)
            sb.setValue(old.get(name, 1.0))
            self.p0_layout.addRow(f"{name} =", sb)
            self.p0_widgets[name] = sb

    def _run(self):
        s = self.series_list[self.target.currentIndex()]
        names = self._param_names()
        if not names:
            QMessageBox.warning(self, "入力エラー", "パラメータ名を入れてください。")
            return
        p0 = [self.p0_widgets[n].value() for n in names]

        try:
            x, y = s.transformed()
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"数式変換で失敗しました: {e}")
            return

        sigma = s.yerr if (self.use_err.isChecked() and s.yerr is not None) else None

        self.setCursor(Qt.WaitCursor)
        try:
            res = fitting.fit(x, y, self.expr.text(), names, p0, sigma=sigma)
        except Exception as e:
            self.output.setPlainText(f"フィットできませんでした。\n\n{e}")
            self.add_btn.setEnabled(False)
            self.result = None
            return
        finally:
            self.unsetCursor()

        self.result = (res, s)
        self.output.setPlainText(res.summary())
        self.add_btn.setEnabled(True)
        # 収束値を初期値欄に書き戻すと、続けて追い込みやすい
        for n, v in zip(names, res.values):
            self.p0_widgets[n].setValue(v)
