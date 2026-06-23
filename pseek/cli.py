import click, re
from pathlib import Path
from .searcher import seek
from .utils import check_rar_backend, compile_regex
from concurrent.futures import ProcessPoolExecutor, TimeoutError
from dataclasses import dataclass


@dataclass
class SearchConfig:
    query: str
    path: Path
    file: bool
    directory: bool
    content: bool
    case_sensitive: bool
    regex: bool
    word: bool
    expr: bool
    timeout: int | None
    fuzzy: bool
    fuzzy_level: int
    ext: set[str]
    exclude_ext: set[str]
    include: set[Path]
    exclude: set[Path]
    re_include: re.Pattern | None
    re_exclude: re.Pattern | None
    max_size: float | None
    min_size: float | None
    archive: bool
    depth: int | None
    arc_ext: set[str]
    arc_ee: set[str]
    arc_inc: set[Path]
    arc_exc: set[Path]
    arc_max: float | None
    arc_min: float | None
    rarfb: str | None
    full_path: bool
    no_content: bool
    
    def __post_init__(self):
        """Post-initialization processing to normalize and validate inputs"""
        self.path = Path(self.path)
        
        # Normalize extensions
        self.ext = set(self.ext)
        self.exclude_ext = (
            set(self.exclude_ext) | {''}
            if self.exclude_ext
            else set()
        )
        self.arc_ext = set(self.arc_ext)
        self.arc_ee = (
            set(self.arc_ee) | {''}
            if self.arc_ee
            else set()
        )
        
        # Normalize include and exclude paths
        self.include = {Path(p).resolve() for p in self.include}
        self.exclude = {Path(p).resolve() for p in self.exclude}
        self.arc_inc = {Path(p) for p in self.arc_inc}
        self.arc_exc = {Path(p) for p in self.arc_exc}
        
        # Compile regex patterns
        self.re_include = compile_regex(self.re_include)
        self.re_exclude = compile_regex(self.re_exclude)


def echo(results: dict) -> int:
    """
    Display the search results with a title.
    Returns the count of results.
    """
    total_results = 0

    for match_type, paths in results.items():
        count_result = 0
        results_title = 'Directories' if match_type == 'directory' else match_type.title() + 's'

        if paths:
            click.echo(click.style(f'\n{results_title}:\n', fg='yellow'))
            if isinstance(paths, dict):
                # For content search results
                for key, value in paths.items():
                    click.echo(key + '\n' + '\n'.join(value) + '\n')
                    count_result += len(value)
            else:
                # For file/directory search results
                count_result = len(paths)
                click.echo('\n'.join(paths))

            if count_result >= 3:
                click.echo(click.style(f'\n{count_result} results found for {match_type}', fg='blue'))

        total_results += count_result

    # Display final summary message.
    message = f'\nTotal results: {total_results}' if total_results else 'No results found'
    click.echo(click.style(message, fg='red'))


@click.command()
@click.argument('query')
@click.option('-p', '--path', type=click.Path(exists=True, file_okay=False, dir_okay=True),
              default='.', show_default=True, help='Base directory to search in.')
# Search type options
@click.option('-f', '--file', is_flag=True, help='Search only in file names.')
@click.option('-d', '--directory', is_flag=True, help='Search only in directory names.')
@click.option('-c', '--content', is_flag=True, help='Search inside file contents.')
# Additional options
@click.option('-C', '--case-sensitive', is_flag=True,
              help='Make the search case-sensitive '
                   '(except when --expr is enabled, '
                   'in which case you can make it case sensitive by putting c before term: c"foo")')
@click.option('-r', '--regex', is_flag=True,
              help='Use regular expressions to search '
                   '(except when --expr is enabled, '
                   'in which case you can make it regex by putting r before term: r"foo")')
@click.option('-w', '--word', is_flag=True,
              help='Match whole words only '
                   '(except when --expr is enabled, '
                   'in which case you can make it match whole word by putting w before term: w"foo")')
@click.option('--expr', is_flag=True,
              help='Enable to write conditions in the query. Example: r"foo.*bar" and ("bar" or "baz") and not "qux" '
                   '(To use regex, word, case-sensitive, and fuzzy features, '
                   'you can use the prefixes r, w, c, and f before terms. Allowed modes: '
                   'r, c, w, f, rc, cr, cw, wc, cf, fc, wf, fw, cwf, cfw, wcf, wfc, fcw, fwc. '
                   'Examples: r"foo.*bar", wcf"Aple", cr".*Foo", ...)')
@click.option('--timeout', type=click.INT,
              help='To stop the search after a specified period of time (Seconds)')
@click.option('--fuzzy', is_flag=True, help='Enable fuzzy search (approximate matching). '
              'except when --expr is enabled, '
              'in which case you can make it fuzzy by putting f before term: f"foo"')
@click.option('--fuzzy-level', type=click.IntRange(0, 99), default=80, show_default=True,
              help='Similarity threshold from 0 to 99 for fuzzy search.')
# Extension filters
@click.option('--ext', multiple=True, type=click.STRING,
              help='Include files with these extensions. Example: --ext py --ext js')
@click.option('-E', '--exclude-ext', multiple=True, type=click.STRING,
              help='Exclude files with these extensions. Example: --exclude-ext jpg --exclude-ext exe')
# Include/Exclude specific paths (files or directories)
@click.option('-i', '--include', type=click.Path(exists=True, file_okay=True, dir_okay=True),
              multiple=True, help='Directories or files to include in search.')
@click.option('-e', '--exclude', type=click.Path(exists=True, file_okay=True, dir_okay=True),
              multiple=True, help='Directories or files to exclude from search.')
@click.option('--re-include', type=click.STRING,
              help='Directories or files to include in search with regex.')
@click.option('--re-exclude', type=click.STRING,
              help='Directories or files to exclude from search with regex.')
# Size filters
@click.option('--max-size', type=click.FLOAT, help='Maximum file/directory size (in MB).')
@click.option('--min-size', type=click.FLOAT, help='Minimum file/directory size (in MB).')
# Archive options
@click.option('--archive', is_flag=True,
              help='Enable search within archive files (e.g. zip, rar, 7z, gz, bz2, xz, tar, tar.gz, tar.bz2, tar.xz)')
@click.option('--depth', type=click.IntRange(min=0), show_default=True,
              help='Maximum archive depth to recurse into (e.g. 2 means only 2 levels).')
@click.option('--arc-ext', multiple=True, type=click.STRING,
              help='Include files with these extensions inside archive files. Example: --arc-ext py --arc-ext js')
@click.option('--arc-ee', multiple=True, type=click.STRING,
              help='Exclude files with these extensions inside archive files. Example: --arc-ee jpg --arc-ee exe')
@click.option('--arc-inc', type=click.Path(file_okay=True, dir_okay=True),
              multiple=True, help='Directories or files to include in search for inside archive files.')
@click.option('--arc-exc', type=click.Path(file_okay=True, dir_okay=True),
              multiple=True, help='Directories or files to exclude from search for inside archive files.')
@click.option('--arc-max', type=click.FLOAT, help='Maximum size of files in the archive (in MB).')
@click.option('--arc-min', type=click.FLOAT, help='Minimum size of files in the archive (in MB).')
@click.option('--rarfb', type=click.Path(exists=True, file_okay=True, dir_okay=False),
              help='Path to RAR backend tool (e.g. UnRAR.exe, ...). '
                   'Enter the file type in the query (e.g. unrar, bsdtar, unar, 7z).')
# Output option
@click.option('--full-path', is_flag=True, help='Display full paths for results.')
@click.option('--no-content', is_flag=True, help='Only display files path for content search.')
def search(**kwargs):
    """Search for files, directories, and file content based on the query."""

    config = SearchConfig(**kwargs)

    check_rar_backend(config.archive, config.rarfb, config.query)

    if not config.expr and config.fuzzy:
        if not config.word:
            click.echo(
                click.style(
                    "Warning: Fuzzy substring highlighting and counting matches are disabled to improve performance.\n",
                    fg="yellow"
                )
            )
        elif config.word and " " in config.query:
            click.echo(
                click.style(
                    'Warning: When using "--fuzzy" and "--word", it is better to have the query be a word and '
                    'not a phrase, as this will cause errors in the results.\n',
                    fg="yellow"
                )
            )

    # If no search type is specified, search in all types.
    if not any((config.file, config.directory, config.content)):
        config.file = config.directory = config.content = True

    # Stop search if it exceeds timeout (It doesn't kill the func and the func continues to execute in the background)
    if config.timeout:
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(seek, config)
            try:
                result = future.result(timeout=config.timeout)
                echo(result)
            except TimeoutError:
                click.echo(
                    click.style(
                        f"Timeout! Search exceeded {config.timeout} seconds and was stopped.",
                        fg="red"
                    )
                )
    else:
        echo(seek(config))


if __name__ == "__main__":
    search()
