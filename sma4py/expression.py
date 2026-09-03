"""数式変換 (X値変換 / Y値変換 / 任意関数の重ね書き) の評価。

Sma4Win の「x を 3 倍したい」といった変換に相当する。
eval を使うが、参照できる名前を明示的に絞ることで安全性を確保している。
"""

import ast

import numpy as np

# 使用を許可する関数群
FUNCS = {
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "asin": np.arcsin, "acos": np.arccos, "atan": np.arctan,
    "atan2": np.arctan2,
    "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh,
    "exp": np.exp, "log": np.log, "ln": np.log, "log10": np.log10,
    "sqrt": np.sqrt, "abs": np.abs, "fabs": np.abs,
    "floor": np.floor, "ceil": np.ceil, "sign": np.sign,
    "pow": np.power, "mod": np.mod,
    "min": np.minimum, "max": np.maximum,
    "erf": None,  # 下で差し替える
}

CONSTS = {"pi": np.pi, "e": np.e}

try:
    from scipy.special import erf as _erf, jn as _jn, yn as _yn, wofz as _wofz
    FUNCS["erf"] = _erf
    FUNCS["jn"] = _jn   # 第1種ベッセル
    FUNCS["yn"] = _yn   # 第2種ベッセル

    def _voigt(x, sigma, gamma):
        """Voigt プロファイル (Faddeeva 関数 wofz による厳密計算)。"""
        z = (np.asarray(x, dtype=float) + 1j * gamma) / (np.asarray(sigma, dtype=float) * np.sqrt(2))
        return np.real(_wofz(z)) / (np.asarray(sigma, dtype=float) * np.sqrt(2 * np.pi))

    FUNCS["voigt"] = _voigt
except ImportError:
    FUNCS.pop("erf")

FUNCS = {k: v for k, v in FUNCS.items() if v is not None}


def diff(y, x):
    """数値微分 (中心差分)。Sma4Win の diff 相当。"""
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    return np.gradient(y, x)


def integ(y, x=None):
    """累積積分。x を省略すると差分の単純累積和になる点も本家と同じ。"""
    y = np.asarray(y, dtype=float)
    if x is None:
        return np.cumsum(y)
    from scipy.integrate import cumulative_trapezoid
    return cumulative_trapezoid(y, np.asarray(x, dtype=float), initial=0.0)


_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Load,
    ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
    ast.USub, ast.UAdd, ast.Compare, ast.Lt, ast.Gt, ast.LtE, ast.GtE,
    ast.Eq, ast.NotEq, ast.Tuple, ast.IfExp,
)


def _validate(node):
    for sub in ast.walk(node):
        if not isinstance(sub, _ALLOWED_NODES):
            raise ValueError(f"この式では使えない構文です: {type(sub).__name__}")
        if isinstance(sub, ast.Name):
            allowed = set(FUNCS) | set(CONSTS) | {"x", "y", "i", "diff", "integ"}
            if sub.id not in allowed:
                raise ValueError(f"未知の名前です: {sub.id}")


def evaluate(expr, x, y=None):
    """expr を評価して ndarray を返す。x, y は元データの配列。

    式の中では x, y のほか i (0 から始まる点番号) が使える。
    """
    if not expr or not expr.strip():
        return None

    x = np.asarray(x, dtype=float)
    tree = ast.parse(expr, mode="eval")
    _validate(tree)

    env = dict(FUNCS)
    env.update(CONSTS)
    env["x"] = x
    env["i"] = np.arange(len(x), dtype=float)
    if y is not None:
        env["y"] = np.asarray(y, dtype=float)
    env["diff"] = lambda v, ref=None: diff(v, x if ref is None else ref)
    env["integ"] = lambda v, ref=None: integ(v, x if ref is None else ref)

    code = compile(tree, "<expr>", "eval")
    result = eval(code, {"__builtins__": {}}, env)  # noqa: S307 - 検証済み
    result = np.asarray(result, dtype=float)
    if result.ndim == 0:
        result = np.full_like(x, float(result))
    return result


def make_function(expr, params):
    """フィッティング用に f(x, *params) を作る。

    expr の中では x と params の各名前 (a, b, c ...) が使える。
    """
    tree = ast.parse(expr, mode="eval")
    for sub in ast.walk(tree):
        if not isinstance(sub, _ALLOWED_NODES):
            raise ValueError(f"この式では使えない構文です: {type(sub).__name__}")
        if isinstance(sub, ast.Name):
            if sub.id not in set(FUNCS) | set(CONSTS) | {"x"} | set(params):
                raise ValueError(f"未知の名前です: {sub.id}")
    code = compile(tree, "<fit>", "eval")

    def f(x, *values):
        env = dict(FUNCS)
        env.update(CONSTS)
        env["x"] = np.asarray(x, dtype=float)
        env.update(dict(zip(params, values)))
        return eval(code, {"__builtins__": {}}, env)  # noqa: S307 - 検証済み

    return f
