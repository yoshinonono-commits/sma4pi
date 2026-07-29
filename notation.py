"""Sma4Win 風のラベル記法を matplotlib の mathtext に変換する。

対応記法
--------
%I : イタリック開始      %R : ローマン(立体)に戻す
%G : ギリシャ文字開始    %A : ギリシャ文字解除
^  : 上付き開始          _  : 下付き開始        @ : 上付き/下付き解除

例:
    "%II%R / A"            -> "$\\mathit{I}\\mathrm{ / A}$"
    "%I%Gl%A%R / nm"       -> "$\\mathit{\\lambda}\\mathrm{ / nm}$"
    "N / m^2"              -> "$\\mathrm{N / m^{2}}$"
    "/10^9@ m"             -> "$\\mathrm{/10^{9} m}$"
"""

GREEK = {
    "a": "alpha", "b": "beta", "g": "gamma", "d": "delta", "e": "epsilon",
    "z": "zeta", "h": "eta", "q": "theta", "i": "iota", "k": "kappa",
    "l": "lambda", "m": "mu", "n": "nu", "x": "xi", "o": "o",
    "p": "pi", "r": "rho", "s": "sigma", "t": "tau", "u": "upsilon",
    "f": "phi", "c": "chi", "y": "psi", "w": "omega",
    "A": "Alpha", "B": "Beta", "G": "Gamma", "D": "Delta", "E": "Epsilon",
    "Z": "Zeta", "H": "Eta", "Q": "Theta", "I": "Iota", "K": "Kappa",
    "L": "Lambda", "M": "Mu", "N": "Nu", "X": "Xi", "O": "O",
    "P": "Pi", "R": "Rho", "S": "Sigma", "T": "Tau", "U": "Upsilon",
    "F": "Phi", "C": "Chi", "Y": "Psi", "W": "Omega",
}

# mathtext が持たない大文字ギリシャ文字は普通のラテン字形で代用する
_NO_GLYPH = {"Alpha": "A", "Beta": "B", "Epsilon": "E", "Zeta": "Z", "Eta": "H",
             "Iota": "I", "Kappa": "K", "Mu": "M", "Nu": "N", "O": "O",
             "Rho": "P", "Tau": "T", "Chi": "X"}

_ESCAPE = {"$": r"\$", "%": r"\%", "&": r"\&", "#": r"\#", "{": r"\{", "}": r"\}"}


class _Run:
    """同じ書体が続く区間。"""

    def __init__(self, italic, greek):
        self.italic = italic
        self.greek = greek
        self.chars = []

    def render(self):
        if not self.chars:
            return ""
        body = "".join(self.chars)
        cmd = r"\mathit" if self.italic else r"\mathrm"
        return cmd + "{" + body + "}"


def to_mathtext(text, wrap=True):
    """Sma4 記法の文字列を mathtext 文字列に変換して返す。"""
    if not text:
        return ""

    italic = False
    greek = False
    runs = [_Run(italic, greek)]
    # 上付き/下付きは「開いた括弧」をスタックで管理する
    open_scripts = 0

    i = 0
    n = len(text)
    while i < n:
        ch = text[i]

        # --- 書体切り替えコマンド ---
        if ch == "%" and i + 1 < n:
            code = text[i + 1]
            if code in "IRGA":
                if code == "I":
                    italic = True
                elif code == "R":
                    italic = False
                elif code == "G":
                    greek = True
                elif code == "A":
                    greek = False
                runs.append(_Run(italic, greek))
                i += 2
                continue

        # --- 上付き / 下付き ---
        if ch in "^_":
            runs[-1].chars.append(ch + "{")
            open_scripts += 1
            i += 1
            continue

        if ch == "@":
            while open_scripts > 0:
                runs[-1].chars.append("}")
                open_scripts -= 1
            i += 1
            continue

        # --- 通常文字 ---
        if greek and ch in GREEK:
            name = GREEK[ch]
            if name in _NO_GLYPH:
                runs[-1].chars.append(_NO_GLYPH[name])
            else:
                runs[-1].chars.append("\\" + name + " ")
        elif ch == " ":
            runs[-1].chars.append(r"\ ")
        elif ch in _ESCAPE:
            runs[-1].chars.append(_ESCAPE[ch])
        else:
            runs[-1].chars.append(ch)
        i += 1

    # 閉じ忘れた上付き/下付きを閉じる
    while open_scripts > 0:
        runs[-1].chars.append("}")
        open_scripts -= 1

    body = "".join(r.render() for r in runs)
    if not body:
        return ""
    return "$" + body + "$" if wrap else body


def preview(text):
    """変換結果を確認したいとき用。失敗しても例外を投げない。"""
    try:
        return to_mathtext(text)
    except Exception:
        return text
