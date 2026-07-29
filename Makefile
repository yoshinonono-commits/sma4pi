# よく使うコマンドの入り口。`make <目標>` で実行する。
# Windows で make が無い場合は、各コマンドを直接打つか setup.ps1 を使う。

PY ?= python

.PHONY: help setup run test clean

help:            ## この一覧を表示
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

setup:           ## 仮想環境を作り依存を入れる
	bash setup.sh

run:             ## アプリを起動 (GUI)
	$(PY) -m sma4py

test:            ## 非GUIテストを実行
	$(PY) tests/test_features.py

clean:           ## キャッシュと仮想環境を削除
	rm -rf .venv build dist *.spec
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
