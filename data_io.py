"""テキスト/CSV データの読み込み。

Sma4Win と同様に「1行1レコード、空白またはカンマ区切りの数値列」を想定し、
先頭の読み飛ばし行数を指定できるようにしてある。
"""

import csv
import io

import numpy as np

_DELIMS = {"auto": None, "whitespace": None, "comma": ",", "tab": "\t"}


def sniff_delimiter(sample):
    """区切り文字を推定する。判別できなければ空白区切りとみなす。"""
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        return dialect.delimiter
    except csv.Error:
        return None  # None は「任意個の空白」を意味する


def load_table(path, skip_rows=0, delimiter="auto", encoding=None):
    """ファイルを読み込み (data, header) を返す。

    data   : (行数, 列数) の float 配列
    header : 列名のリスト。ヘッダ行が無ければ "Col 1", "Col 2" ... を生成する
    """
    encodings = [encoding] if encoding else ["utf-8", "cp932", "latin-1"]
    text = None
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                text = f.read()
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("文字コードを判別できませんでした。")

    lines = text.splitlines()[skip_rows:]
    lines = [ln for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines:
        raise ValueError("読み込めるデータ行がありません。")

    if delimiter == "auto":
        delim = sniff_delimiter("\n".join(lines[:5]))
    else:
        delim = _DELIMS.get(delimiter)

    header = None
    first = _split(lines[0], delim)
    if not _all_numeric(first):
        header = first
        lines = lines[1:]
        if not lines:
            raise ValueError("ヘッダ行しかありません。")

    rows = []
    for ln in lines:
        parts = _split(ln, delim)
        try:
            rows.append([float(p) for p in parts])
        except ValueError:
            continue  # 数値化できない行は読み飛ばす

    if not rows:
        raise ValueError("数値として解釈できる行がありません。")

    width = max(len(r) for r in rows)
    padded = [r + [np.nan] * (width - len(r)) for r in rows]
    data = np.array(padded, dtype=float)

    if header is None or len(header) != width:
        header = [f"Col {i + 1}" for i in range(width)]
    return data, header


def _split(line, delim):
    if delim is None:
        return line.split()
    return [p.strip() for p in line.split(delim)]


def _all_numeric(parts):
    if not parts:
        return False
    for p in parts:
        try:
            float(p)
        except ValueError:
            return False
    return True


def load_from_string(text, **kwargs):
    """テスト用: 文字列から読み込む。"""
    buf = io.StringIO(text)
    lines = buf.read()
    import tempfile
    import os
    fd, tmp = tempfile.mkstemp(suffix=".txt", text=True)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(lines)
    try:
        return load_table(tmp, **kwargs)
    finally:
        os.unlink(tmp)
