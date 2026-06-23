# Pseek

## Overview

A powerful command-line tool for searching files, directories, and content inside files efficiently. The tool supports searching by name, content, extensions, and more with advanced filtering options.

## Features

* **Search in file & folder names**
* **Search inside file contents**
* **Highlight matches** in terminal output
* **Optimized for speed** with ThreadPoolExecutor
* Support **logical expression** for search queries
* Search inside **archive files** (e.g. `zip`, `rar`, `7z`, `gz`, `bz2`, `xz`, `tar`, `tar.gz`, `tar.bz2`, `tar.xz`)
* **Cross-platform** (Linux, macOS, Windows)

## Installation

### **`1` Install via `pip` (Recommended)**

```sh
pip install pseek
```

### **`2` Install from source**

```sh
git clone https://github.com/ArianN8610/pysearch.git
cd pysearch
python -m venv venv
[Activate venv]
pip install click==8.1.8 lark==1.2.2 py7zr==1.0.0 rarfile==4.2 rapidfuzz==3.13.0
```

## Usage

Run the command with a search query:
```sh
psk <query> [options]
```

## Examples

### Search for a keyword in file & folder names

```sh
psk "my_keyword" --path /path/to/search --file --directory
```

### Search inside file contents

```sh
psk "error" --path /var/logs --content
```

### Search only in specific file types

```sh
psk "TODO" --path ./projects --ext py --ext txt
```

### Search by regex

```sh
psk "error\d+" --regex
```

## Command Options

| Option                           | Description                                                                                                                                                                                                                                                      |
|----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--path`                         | Base directory to search in (default: current directory `.`)                                                                                                                                                                                                     |
| `--file`                         | Search only in file names                                                                                                                                                                                                                                        |
| `--directory`                    | Search only in directory names                                                                                                                                                                                                                                   |
| `--content`                      | Search within file contents                                                                                                                                                                                                                                      |
| `--ext`, `--exclude-ext`         | Filter by file extension (e.g., `txt`, `log`)                                                                                                                                                                                                                    |
| `--case-sensitive`               | Make the search case-sensitive (except when `--expr` is enabled, in which case you can make it case sensitive by putting `c` before term: `c"foo"`)                                                                                                              |
| `--regex`                        | Use regular expressions to search (except when `--expr` is enabled, in which case you can make it regex by putting `r` before term: `r"foo"`)                                                                                                                    |
| `--include`, `--exclude`         | Limit search results to specific set of directories or files                                                                                                                                                                                                     |
| `--re-include`, `--re-exclude`   | Limit search results to specific directories or files with regex                                                                                                                                                                                                 |
| `--word`                         | Match the whole word only (except when `--expr` is enabled, in which case you can make it match whole word by putting `w` before term: `w"foo"`)                                                                                                                 |
| `--expr`                         | Enable boolean query expressions. Example: r"foo.*bar" and ("bar" or "baz") and not "qux". Prefixes: r=regex, c=case-sensitive, w=whole-word, f=fuzzy                                                                                                            |
| `--timeout`                      | Stop the search after the specified number of seconds                                                                                                                                                                                                            |
| `--fuzzy`                        | Enable fuzzy search (Highlighting and counting matches are disabled in this mode if `--word` is not enabled to prevent the program from slowing down). except when `--expr` is enabled, in which case you can make it fuzzy by putting `f` before term: `f"foo"` |
| `--fuzzy-level`                  | Fuzzy matching threshold (0-99). Higher values require closer matches (default: `80`)                                                                                                                                                                            |
| `--max-size`, `--min-size`       | Specify maximum and minimum sizes for files and directories                                                                                                                                                                                                      |
| `--archive`                      | Enable search within archive files (e.g. `zip`, `rar`, `7z`, `gz`, `bz2`, `xz`, `tar`, `tar.gz`, `tar.bz2`, `tar.xz`)                                                                                                                                            |
| `--depth`                        | Maximum nested archive depth. Example: 2 allows searching up to two archive levels                                                                                                                                                                               |
| `--arc-ext`, `--arc-exc-ext`     | Filter by file extension inside archive files                                                                                                                                                                                                                    |
| `--arc-include`, `--arc-exclude` | Limit search results to specific set of directories or files inside archive files                                                                                                                                                                                |
| `--arc-max`, `--arc-min`         | Specify maximum and minimum sizes for files inside archive files (It doesn't work for directories because their size is zero in archive files)                                                                                                                   |
| `--rar-backend`                  | Path to RAR backend tool (e.g. UnRAR.exe, ...)                                                                                                                                                                                                                   |
| `--full-path`                    | Display full path of files and directories                                                                                                                                                                                                                       |
| `--paths-only`                   | Only show matching file paths for content search                                                                                                                                                                                                                 |

## Requirements

* Python 3.6 or higher
* `unrar`, `bsdtar`, `unar` or `7zip` for the [rarfile](https://pypi.org/project/rarfile/) library to support searching inside `.rar` files (optional)
