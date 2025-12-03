# remove_unuse_image

このリポジトリには、Markdown ファイルの `.assets` フォルダ内で使用されていない画像ファイルを削除するスクリプト `rmassets.py` が含まれます。

使い方:

```
python rmassets.py test.md        # 対話式で未使用ファイルを削除
python rmassets.py test.md --dry-run
python rmassets.py . --yes        # カレントディレクトリ内の .md を全て処理、確認なしで削除
```

挙動:

- `X.md` に対して `X.assets/` を資産ディレクトリとして扱います。
- Markdown の `![](...)` と HTML の `<img src="...">`、および参照定義 `[id]: url` を走査して参照されている画像を検出します。
- `.assets` フォルダ直下のファイルのうち、参照されていないファイルを削除します（サブディレクトリは対象外）。

注意:

- 簡易的なパーシングを使用しているため、極めて特殊なケースは検出できない可能性があります。
- 重要なファイルは必ず `--dry-run` で確認してください。
