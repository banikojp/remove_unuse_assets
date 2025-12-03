"""Remove unused images from a Markdown file's `.assets` folder.

Usage examples:
  python rmassets.py test.md         # interactive - will ask before deleting
  python rmassets.py test.md --dry-run
  python rmassets.py . --yes         # process all .md files in current dir without prompting

Behavior:
  For a markdown file `X.md` this script treats `X.assets/` as the assets folder.
  It parses the markdown for image references (markdown image syntax and HTML <img>). If
  an asset file in the asset folder is not referenced anywhere in the markdown it will
  be deleted (unless `--dry-run` is used).

Notes:
  - Only files directly under the `.assets` folder are considered for deletion (no recursive removal).
  - The script is conservative about parsing; it matches common image syntaxes and reference-style links.
"""

from __future__ import annotations

import argparse
import os
import re
from typing import Iterable, List, Set


def find_markdown_files(paths: Iterable[str]) -> List[str]:
	results: List[str] = []
	for p in paths:
		if os.path.isdir(p):
			for name in os.listdir(p):
				if name.lower().endswith(".md"):
					results.append(os.path.join(p, name))
		elif os.path.isfile(p) and p.lower().endswith(".md"):
			results.append(p)
		else:
			print(f"Warning: ignoring {p} (not a .md file or directory)")
	return sorted(results)


def read_text(path: str) -> str:
	with open(path, "r", encoding="utf-8") as f:
		return f.read()


def extract_image_paths(markdown: str) -> Set[str]:
	"""Extract image paths referenced in markdown text.

	Returns a set of basenames (file names) that appear referenced.
	"""
	refs: Set[str] = set()

	# Markdown image: ![alt](path "title")
	md_image_re = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
	for m in md_image_re.finditer(markdown):
		raw = m.group(1).strip()
		# strip surrounding < > if present
		if raw.startswith("<") and raw.endswith(">"):
			raw = raw[1:-1].strip()
		if " " in raw and (raw.count("\"") < 2 and raw.count("'") < 2):
			raw = raw.split()[0]
		refs.add(os.path.basename(raw))

	# HTML <img src="..."> or <img src='...'>
	html_img_re = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)
	for m in html_img_re.finditer(markdown):
		refs.add(os.path.basename(m.group(1).strip()))

	# Reference-style definitions: [id]: url
	ref_def_re = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.MULTILINE)
	for m in ref_def_re.finditer(markdown):
		refs.add(os.path.basename(m.group(1).strip()))

	# Also capture bare URLs that contain asset folder name like "something.assets/name.png"
	asset_like_re = re.compile(r"[\w\-./\\]+\.assets[/\\]([\w.\- %()+,]+)\)")
	for m in asset_like_re.finditer(markdown):
		refs.add(os.path.basename(m.group(1)))

	# Remove empty
	refs.discard("")
	return refs


def process_markdown(md_path: str, dry_run: bool = False, assume_yes: bool = False) -> int:
	"""Process a single markdown file. Returns number of deleted files."""
	text = read_text(md_path)
	referenced = extract_image_paths(text)

	base, _ = os.path.splitext(md_path)
	asset_dir = base + ".assets"
	if not os.path.isdir(asset_dir):
		print(f"No asset directory for {md_path}: {asset_dir} (skipped)")
		return 0

	all_files = [f for f in os.listdir(asset_dir) if os.path.isfile(os.path.join(asset_dir, f))]
	if not all_files:
		print(f"No files in asset directory {asset_dir}")
		return 0

	unused = [f for f in all_files if f not in referenced]

	if not unused:
		print(f"No unused files in {asset_dir}")
		return 0

	print(f"Asset dir: {asset_dir}")
	print(f"Referenced files ({len(referenced)}): {', '.join(sorted(referenced)) if referenced else '(none)'}")
	print(f"Unused files ({len(unused)}):")
	for f in unused:
		print(f"  {f}")

	if dry_run:
		print("Dry run: no files will be deleted.")
		return 0

	if not assume_yes:
		ans = input("Delete the above files? [y/N]: ").strip().lower()
		if ans not in ("y", "yes"):
			print("Aborted by user.")
			return 0

	deleted = 0
	for f in unused:
		fp = os.path.join(asset_dir, f)
		try:
			os.remove(fp)
			deleted += 1
			print(f"Deleted: {fp}")
		except Exception as e:
			print(f"Failed to delete {fp}: {e}")

	return deleted


def main(argv: List[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Remove unused images from markdown .assets folders")
	parser.add_argument("paths", nargs="+", help="Markdown files or directories to process")
	parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without removing files")
	parser.add_argument("--yes", action="store_true", help="Do not prompt; delete files")
	args = parser.parse_args(argv)

	md_files = find_markdown_files(args.paths)
	if not md_files:
		print("No markdown files found to process.")
		return 1

	total_deleted = 0
	for md in md_files:
		try:
			deleted = process_markdown(md, dry_run=args.dry_run, assume_yes=args.yes)
			total_deleted += deleted
		except Exception as e:
			print(f"Error processing {md}: {e}")

	print(f"Finished. Total files deleted: {total_deleted}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
