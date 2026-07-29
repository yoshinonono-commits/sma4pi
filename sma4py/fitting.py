"""最小二乗フィッティング。"""

import numpy as np
from scipy.optimize import curve_fit

from .expression import make_function

# よく使う関数のプリセット (表示名, 式, パラメータ名, 初期値の推定関数)
PRESETS = [
    ("直線 a + b*x", "a + b*x", ["a", "b"]),
    ("2次 a + b*x + c*x^2", "a + b*x + c*x**2", ["a", "b", "c"]),
    ("指数 a*exp(b*x)", "a*exp(b*x)", ["a", "b"]),
    ("指数+定数 a + b*exp(c*x)", "a + b*exp(c*x)", ["a", "b", "c"]),
    ("べき乗 a*x^b", "a*x**b", ["a", "b"]),
    ("ガウス a*exp(-((x-b)/c)^2)", "a*exp(-((x-b)/c)**2)", ["a", "b", "c"]),
    ("ローレンツ a/((x-b)^2+c)", "a/((x-b)**2+c)", ["a", "b", "c"]),
    ("対数 a + b*log(x)", "a + b*log(x)", ["a", "b"]),
    ("Voigt a*voigt(x-b,s,g)", "a*voigt(x-b, s, g)", ["a", "b", "s", "g"]),
]

# 多重ピークの組み立てに使う形状テンプレート。
# 値は (パラメータ名の並び, 1ピーク分の式テンプレート)。
PEAK_SHAPES = {
    "ガウス": (["a", "b", "c"], "{a}*exp(-((x-{b})/{c})**2)"),
    "ローレンツ": (["a", "b", "c"], "{a}/((x-{b})**2+{c})"),
    "Voigt": (["a", "b", "s", "g"], "{a}*voigt(x-{b}, {s}, {g})"),
}


def build_multipeak(shape, n, baseline=True):
    """shape (PEAK_SHAPES のキー) を n 個足し合わせた式を組み立てる。

    baseline が True なら定数項 d0 を先頭に加える。(expr, params) を返す。
    """
    if shape not in PEAK_SHAPES:
        raise ValueError(f"未知のピーク形状です: {shape}")
    names, template = PEAK_SHAPES[shape]

    terms = []
    params = []
    for i in range(1, n + 1):
        sub = {name: f"{name}{i}" for name in names}
        terms.append(template.format(**sub))
        params.extend(sub[name] for name in names)

    expr = " + ".join(terms)
    if baseline:
        expr = "d0 + " + expr
        params = ["d0"] + params
    return expr, params


class FitResult:
    def __init__(self, expr, params, values, errors, chi2, r2, npoints):
        self.expr = expr
        self.params = params
        self.values = values
        self.errors = errors
        self.chi2 = chi2
        self.r2 = r2
        self.npoints = npoints

    def summary(self):
        lines = [f"式: y = {self.expr}", f"データ点数: {self.npoints}", ""]
        for name, v, e in zip(self.params, self.values, self.errors):
            if np.isfinite(e):
                lines.append(f"{name} = {v:.6g}  ± {e:.3g}")
            else:
                lines.append(f"{name} = {v:.6g}")
        lines.append("")
        lines.append(f"χ² (残差二乗和) = {self.chi2:.6g}")
        lines.append(f"決定係数 R²     = {self.r2:.6f}")
        return "\n".join(lines)

    def curve(self, x):
        f = make_function(self.expr, self.params)
        return f(np.asarray(x, dtype=float), *self.values)


def fit(x, y, expr, params, p0, sigma=None, maxfev=20000):
    """任意関数で最小二乗フィッティングを行い FitResult を返す。"""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    good = np.isfinite(x) & np.isfinite(y)
    x, y = x[good], y[good]
    if sigma is not None:
        sigma = np.asarray(sigma, dtype=float)[good]

    if len(x) < len(params):
        raise ValueError(
            f"データ点が {len(x)} 個しかなく、パラメータ {len(params)} 個を決められません。"
        )

    f = make_function(expr, params)

    # 初期値で一度評価し、式が壊れていないか先に確かめる
    try:
        test = f(x, *p0)
        test = np.asarray(test, dtype=float)
        if not np.all(np.isfinite(test)):
            raise ValueError(
                "初期値で計算すると無限大または NaN になります。初期値を見直してください。"
            )
    except ZeroDivisionError:
        raise ValueError("初期値でゼロ除算が起きました。初期値を見直してください。")

    with np.errstate(all="ignore"):
        popt, pcov = curve_fit(
            f, x, y, p0=list(p0), sigma=sigma,
            absolute_sigma=sigma is not None, maxfev=maxfev,
        )

    if pcov is None or not np.all(np.isfinite(pcov)):
        perr = np.full(len(params), np.nan)
    else:
        perr = np.sqrt(np.abs(np.diag(pcov)))

    resid = y - np.asarray(f(x, *popt), dtype=float)
    chi2 = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - chi2 / ss_tot if ss_tot > 0 else float("nan")

    return FitResult(expr, list(params), list(popt), list(perr), chi2, r2, len(x))


def guess_p0(x, y, params):
    """初期値の当たりを付ける。あくまで出発点。"""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    guesses = []
    for name in params:
        if name == "a":
            guesses.append(float(np.nanmean(y)) or 1.0)
        elif name == "b":
            guesses.append(1.0)
        else:
            guesses.append(1.0)
    return guesses
