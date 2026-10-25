"""Report compiler warnings that land in this repository's own code from an ESPHome build.

A lambda is a fragment that only compiles inside the generated main.cpp, so the lint reads the
build ESPHome already produced rather than generating C++ itself. For each build it reruns the
compile of main.cpp, and of any other translation unit this repository authored, syntax-only with
the build's own flags plus a few stricter warnings. It keeps the diagnostics located in this
repository's code and drops the rest, which belong to ESPHome, the framework, or a library.

A diagnostic is this repository's when it lands in one of these places:
  - a line of a YAML lambda, which ESPHome copies into main.cpp after a #line directive
  - a lambda ESPHome inlined as a bare expression, found by searching the YAML for it
  - a C/C++ file under the config root, or a copy of one in the build tree, matched by content

Run it on any route that runs the ESPHome CLI, here the container with the config tree at /config,
either compiling a config first or against a build already compiled:
  PYTHONPATH=/config/tools/compile-lint/src python3 -m compile_lint --config-root /config \\
    --compile /config/test/<template>.yaml
  PYTHONPATH=/config/tools/compile-lint/src python3 -m compile_lint --config-root /config \\
    /cache/build/<node>

Exit status is 0 when nothing was found, 1 when a warning or error landed in owned code, and 2
when the lint could not run, such as a failed compile or a build with no compile database.
"""

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

# Stricter than the build's own -Wall -Wextra set, and limited to warnings a YAML author can fix.
# Leave out -Wshadow, which fires on ESPHome's nested script parameters that no YAML can reach.
DEFAULT_FLAGS = ["-Wdouble-promotion"]

SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".ipp", ".tcc"}

# Dependency-file and output options would make the recheck overwrite the build's own outputs.
DROPPED_WITH_VALUE = {"-o", "-MF", "-MT", "-MQ"}
DROPPED = {"-c", "-MD", "-MMD", "-MP"}
COMPILER_WRAPPERS = {"ccache", "sccache"}

DIAGNOSTIC = re.compile(
    r"^(?P<path>[^:\n]+):(?P<line>\d+):(?P<column>\d+): (?P<severity>warning|error): "
    r"(?P<message>.*)$"
)
LINE_DIRECTIVE = re.compile(r'^\s*#line\s+(?P<line>\d+)\s+"(?P<path>[^"]+)"')
# The rewrites ESPHome applies to lambda text before it emits it, tried in this order.
# - A substitution, ${name} or $name, which the generated code carries resolved.
# - An id(name) before a member access, which becomes name->.
# - A bare id(name), which becomes name, or name->value() for a global.
REWRITE = re.compile(
    r"(?P<substitution>\$\{[^}]*\}|\$[A-Za-z_]\w*)"
    r"|\bid\(\s*(?P<member>[\w${}]+)\s*\)\."
    r"|\bid\(\s*(?P<bare>[\w${}]+)\s*\)"
)
# ESPHome blanks comments in the copy, so a trailing one on a lambda line is not compared.
TRAILING_COMMENT = re.compile(r"\s*//[^\"']*$")
RETURN_EXPRESSION = re.compile(r"^return\s+(?P<expression>[^;]+);?$")
BARE_TOKEN = re.compile(r"^[\w.]+$")
BUILD_PATH = re.compile(r"Build path: (?P<path>\S+)")


@dataclass(frozen=True)
class Diagnostic:
    """One compiler diagnostic as the compiler printed it."""

    path: str
    line: int
    column: int
    severity: str
    message: str


@dataclass(frozen=True, order=True)
class Finding:
    """A diagnostic located in this repository's code, with a repository-relative path."""

    path: str
    line: int
    column: int
    severity: str
    message: str


@dataclass(frozen=True)
class Scalar:
    """A YAML scalar's 1-based line span and its text."""

    start: int
    end: int
    text: str


@dataclass(frozen=True)
class Directive:
    """A #line directive in main.cpp: its own 0-based index, and the YAML line it names."""

    index: int
    line: int
    path: str


@dataclass
class BuildResult:
    """What one build's lint found, and the diagnostics it set aside as not owned."""

    node: str
    findings: list[Finding] = field(default_factory=lambda: list[Finding]())
    ignored: list[Diagnostic] = field(default_factory=lambda: list[Diagnostic]())


class LintError(Exception):
    """The lint could not run against a build."""


def parse_diagnostics(text: str) -> list[Diagnostic]:
    """Return every warning and error line in compiler output, skipping notes and context."""
    found: list[Diagnostic] = []
    for raw in text.splitlines():
        match = DIAGNOSTIC.match(raw)
        if match:
            found.append(
                Diagnostic(
                    path=match["path"],
                    line=int(match["line"]),
                    column=int(match["column"]),
                    severity=match["severity"],
                    message=match["message"],
                )
            )
    return found


def entry_arguments(entry: dict[str, Any]) -> list[str]:
    """Return a compile database entry's command as an argument list."""
    if "arguments" in entry:
        return [str(a) for a in cast(list[Any], entry["arguments"])]
    return shlex.split(str(entry["command"]))


def syntax_only_arguments(arguments: list[str], flags: list[str]) -> list[str]:
    """Turn a compile command into a syntax-only compile with extra warning flags."""
    # A compiler cache gains nothing on a syntax-only compile, and its store may not be writable.
    if arguments and Path(arguments[0]).name in COMPILER_WRAPPERS:
        arguments = arguments[1:]
    kept: list[str] = []
    skip = False
    for argument in arguments:
        if skip:
            skip = False
        elif argument in DROPPED_WITH_VALUE:
            skip = True
        elif argument in DROPPED or argument.startswith("-fdiagnostics-color"):
            continue
        else:
            kept.append(argument)
    return [
        *kept,
        "-fsyntax-only",
        "-fdiagnostics-color=never",
        "-fno-diagnostics-show-caret",
        *flags,
    ]


def replace_source(arguments: list[str], entry: dict[str, Any], replacement: Path) -> list[str]:
    """Point a compile command at another source file, keeping the original's quoted includes."""
    source = entry_path(entry)
    replaced: list[str] = []
    found = False
    for argument in arguments:
        absolute = Path(os.path.normpath(Path(str(entry["directory"])) / argument))
        if not argument.startswith("-") and absolute == source:
            replaced.append(str(replacement))
            found = True
        else:
            replaced.append(argument)
    if not found:
        raise LintError(f"{source}: the compile command does not name its own source file")
    return [*replaced, "-iquote", str(source.parent)]


def load_compile_database(path: Path) -> list[dict[str, Any]]:
    """Read a compile database."""
    return cast(list[dict[str, Any]], json.loads(path.read_text(encoding="utf-8")))


def entry_path(entry: dict[str, Any]) -> Path:
    """Return a compile database entry's source file as an absolute path."""
    return Path(os.path.normpath(Path(str(entry["directory"])) / str(entry["file"])))


def is_main(entry: dict[str, Any]) -> bool:
    """Say whether an entry compiles the generated main.cpp."""
    path = entry_path(entry)
    return path.name == "main.cpp" and path.parent.name == "src"


def find_compile_database(build: Path) -> Path:
    """Return the compile database under a build directory that holds the app's main.cpp."""
    for candidate in sorted(build.rglob("compile_commands.json")):
        if "bootloader" in candidate.parts:
            continue
        if any(is_main(entry) for entry in load_compile_database(candidate)):
            return candidate
    raise LintError(f"{build}: no compile_commands.json with a main.cpp entry, compile it first")


def content_hash(path: Path) -> str:
    """Return a file's SHA-256, used to recognize a repository file copied into the build."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk_files(root: Path, suffixes: set[str]) -> Iterator[Path]:
    """Yield files with one of the suffixes, skipping dot directories and the retired archive."""
    for directory, names, files in os.walk(root):
        names[:] = sorted(n for n in names if not n.startswith(".") and n != "archive")
        for name in sorted(files):
            if Path(name).suffix in suffixes:
                yield Path(directory) / name


def owned_sources(root: Path) -> dict[str, str]:
    """Map the content hash of every C/C++ file in the repository to its relative path."""
    return {
        content_hash(p): p.relative_to(root).as_posix() for p in walk_files(root, SOURCE_SUFFIXES)
    }


def relative_to_root(path: Path, root: Path) -> str | None:
    """Return a path relative to the config root, or None when it lies outside it."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return None


def yaml_scalars(path: Path) -> list[Scalar]:
    """Return every scalar in a YAML file with its line span, tags and all left unresolved."""
    scalars: list[Scalar] = []

    def walk(node: yaml.Node) -> None:
        if isinstance(node, yaml.ScalarNode):
            start = node.start_mark.line + 1
            end = node.end_mark.line + (1 if node.end_mark.column > 0 else 0)
            scalars.append(Scalar(start=start, end=max(start, end), text=str(node.value)))
        elif isinstance(node, yaml.SequenceNode):
            for child in cast(list[yaml.Node], node.value):
                walk(child)
        elif isinstance(node, yaml.MappingNode):
            for key, value in cast(list[tuple[yaml.Node, yaml.Node]], node.value):
                walk(key)
                walk(value)

    # Composing builds the node tree without constructing values, so ESPHome's own tags such as
    # !include, !secret, and !lambda need no constructor.
    with path.open(encoding="utf-8") as stream:
        loader = yaml.SafeLoader(stream)
        try:
            while loader.check_node():
                document = loader.get_node()
                if document is not None:
                    walk(document)
        finally:
            loader.dispose()
    return scalars


class YamlIndex:
    """Caches each repository YAML file's scalars, read on first use."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._scalars: dict[str, list[Scalar]] = {}

    def scalars(self, relative: str) -> list[Scalar]:
        if relative not in self._scalars:
            try:
                self._scalars[relative] = yaml_scalars(self.root / relative)
            except (OSError, yaml.YAMLError) as error:
                print(f"compile-lint: cannot read {relative}: {error}", file=sys.stderr)
                self._scalars[relative] = []
        return self._scalars[relative]

    def all_files(self) -> list[str]:
        return [
            p.relative_to(self.root).as_posix() for p in walk_files(self.root, {".yaml", ".yml"})
        ]


def normalize(text: str) -> str:
    """Collapse whitespace, so text matches however the generator spaced it."""
    return " ".join(text.split())


def lambda_pattern(text: str) -> re.Pattern[str]:
    """Return a pattern for YAML lambda text that matches the C++ ESPHome generates from it."""
    pieces: list[str] = []
    position = 0
    text = normalize(text)
    for match in REWRITE.finditer(text):
        pieces.append(re.escape(text[position : match.start()]))
        if match["substitution"]:
            pieces.append(".+?")
        elif match["member"]:
            pieces.append(lambda_pattern(match["member"]).pattern + "->")
        else:
            pieces.append(lambda_pattern(match["bare"]).pattern + r"(?:->value\(\))?")
        position = match.end()
    pieces.append(re.escape(text[position:]))
    return re.compile("".join(pieces))


def lambda_line(scalar: Scalar, directive: Directive, offset: int) -> tuple[int, str] | None:
    """Return the YAML line and text a generated line copies, offset lines after a directive.

    ESPHome numbers a lambda's #line one past the scalar's first line. A block scalar's body
    starts on that line, so its body maps line for line, while a lambda written inline after its
    key is the scalar's only line.
    """
    if scalar.start + 1 != directive.line:
        return None
    lines = scalar.text.splitlines()
    if scalar.start == scalar.end:
        return (scalar.start, scalar.text) if offset == 0 else None
    if offset >= len(lines):
        return None
    return directive.line + offset, lines[offset]


def inline_expressions(scalars: list[Scalar]) -> Iterator[tuple[Scalar, re.Pattern[str]]]:
    """Yield the single-expression lambdas ESPHome may inline as a bare expression."""
    for scalar in scalars:
        match = RETURN_EXPRESSION.match(normalize(scalar.text))
        if match:
            expression = match["expression"].strip()
            # A bare name or number would match any generated line that mentions it.
            if not BARE_TOKEN.match(expression):
                yield scalar, lambda_pattern(expression)


class BuildLint:
    """Lints one ESPHome build directory against the repository at the config root."""

    def __init__(self, build: Path, root: Path, flags: list[str], owned: dict[str, str]) -> None:
        self.build = build
        self.root = root
        self.flags = flags
        self.owned = owned
        self.index = YamlIndex(root)
        self.main_lines: list[str] = []
        self.directives: list[Directive] = []

    def run(self) -> BuildResult:
        database = find_compile_database(self.build)
        result = BuildResult(node=self.build.name)
        seen: set[Finding] = set()
        for entry in load_compile_database(database):
            if is_main(entry):
                diagnostics = self.compile_main(entry)
            elif self.owned_path(entry_path(entry)) is not None:
                diagnostics = self.compile(entry, entry_arguments(entry))
            else:
                continue
            for diagnostic in diagnostics:
                findings = list(self.classify(diagnostic, Path(str(entry["directory"]))))
                if not findings:
                    result.ignored.append(diagnostic)
                for finding in findings:
                    if finding not in seen:
                        seen.add(finding)
                        result.findings.append(finding)
        result.findings.sort()
        return result

    def compile_main(self, entry: dict[str, Any]) -> list[Diagnostic]:
        """Compile main.cpp with its #line directives blanked, so diagnostics keep its lines.

        ESPHome never resets #line after a lambda or an LVGL widget, so with the directives in
        place, generated code after one is reported against YAML lines it did not come from.
        """
        source = entry_path(entry)
        self.main_lines = source.read_text(encoding="utf-8").splitlines()
        self.directives = []
        blanked: list[str] = []
        for index, text in enumerate(self.main_lines):
            match = LINE_DIRECTIVE.match(text)
            relative = (
                relative_to_root(Path(os.path.normpath(match["path"])), self.root)
                if match
                else None
            )
            if match and relative is not None:
                self.directives.append(Directive(index, int(match["line"]), relative))
            blanked.append("" if match else text)
        with tempfile.TemporaryDirectory(prefix="compile-lint-") as scratch:
            copy = Path(scratch) / "main.cpp"
            copy.write_text("\n".join(blanked) + "\n", encoding="utf-8")
            diagnostics = self.compile(entry, replace_source(entry_arguments(entry), entry, copy))
        return [
            Diagnostic(str(source), d.line, d.column, d.severity, d.message)
            if Path(d.path) == copy
            else d
            for d in diagnostics
        ]

    def compile(self, entry: dict[str, Any], arguments: list[str]) -> list[Diagnostic]:
        try:
            completed = subprocess.run(
                syntax_only_arguments(arguments, self.flags),
                cwd=str(entry["directory"]),
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise LintError(f"{self.build.name}: cannot run the compiler: {error}") from error
        diagnostics = parse_diagnostics(completed.stderr)
        if completed.returncode != 0 and not any(d.severity == "error" for d in diagnostics):
            raise LintError(
                f"{self.build.name}: the syntax-only compile of {entry['file']} failed "
                f"with no diagnostic:\n{completed.stderr}"
            )
        return diagnostics

    def owned_path(self, path: Path) -> str | None:
        """Return the repository path a source or header is, directly or as a build copy."""
        relative = relative_to_root(path, self.root)
        if relative is not None:
            return relative
        if path.suffix in SOURCE_SUFFIXES and path.is_file():
            return self.owned.get(content_hash(path))
        return None

    def classify(self, diagnostic: Diagnostic, directory: Path) -> Iterator[Finding]:
        """Yield the findings a diagnostic stands for, none when it is not this repository's."""
        path = Path(os.path.normpath(directory / diagnostic.path))
        if path.name == "main.cpp" and path.parent.name == "src" and self.main_lines:
            yield from self.classify_main(diagnostic)
            return
        relative = self.owned_path(path)
        if relative is not None:
            yield Finding(
                relative,
                diagnostic.line,
                diagnostic.column,
                diagnostic.severity,
                diagnostic.message,
            )

    def classify_main(self, diagnostic: Diagnostic) -> Iterator[Finding]:
        """Attribute a diagnostic in main.cpp to the YAML lambda line it was copied from."""
        index = diagnostic.line - 1
        if not 0 <= index < len(self.main_lines):
            return
        generated = normalize(self.main_lines[index])
        preceding = [d for d in self.directives if d.index < index]
        if preceding:
            directive = preceding[-1]
            for scalar in self.index.scalars(directive.path):
                located = lambda_line(scalar, directive, index - directive.index - 1)
                if located is None:
                    continue
                line, text = located
                if lambda_pattern(TRAILING_COMMENT.sub("", text)).fullmatch(generated):
                    # The generated column counts ESPHome's indentation and rewrites, not the YAML's.
                    yield Finding(directive.path, line, 1, diagnostic.severity, diagnostic.message)
                    return
        yield from self.match_inline(diagnostic, generated)

    def match_inline(self, diagnostic: Diagnostic, generated: str) -> Iterator[Finding]:
        """Attribute a diagnostic to the YAML lambdas whose expression ESPHome inlined there."""
        node_files = list(dict.fromkeys(d.path for d in self.directives))
        for candidates in (node_files, self.index.all_files()):
            matches = [
                Finding(relative, scalar.start, 1, diagnostic.severity, diagnostic.message)
                for relative in candidates
                for scalar, pattern in inline_expressions(self.index.scalars(relative))
                if pattern.search(generated)
            ]
            if matches:
                yield from matches
                return


def escape_data(text: str) -> str:
    """Escape a workflow command's message."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def escape_property(text: str) -> str:
    """Escape a workflow command's property value."""
    return escape_data(text).replace(":", "%3A").replace(",", "%2C")


def annotation(node: str, finding: Finding) -> str:
    """Return the workflow command that annotates a finding on its file and line."""
    level = "error" if finding.severity == "error" else "warning"
    properties = ",".join(
        [
            f"file={escape_property(finding.path)}",
            f"line={finding.line}",
            f"col={finding.column}",
            f"title={escape_property(f'compile-lint {node}')}",
        ]
    )
    return f"::{level} {properties}::{escape_data(finding.message)}"


def summary(results: list[BuildResult]) -> str:
    """Return the Markdown the workflow step summary shows."""
    rows = [
        f"| `{r.node}` | `{f.path}:{f.line}:{f.column}` | {f.severity} | "
        f"{f.message.replace('|', '\\|')} |"
        for r in results
        for f in r.findings
    ]
    if not rows:
        nodes = ", ".join(f"`{r.node}`" for r in results)
        return f"### Compile lint\n\nNo warnings in this repository's code for {nodes}.\n"
    header = [
        "### Compile lint",
        "",
        "| Node | Location | Severity | Message |",
        "| --- | --- | --- | --- |",
    ]
    return "\n".join([*header, *rows, ""])


def compile_config(config: Path) -> Path:
    """Compile a config with the ESPHome CLI, echoing its output, and return its build path."""
    try:
        process = subprocess.Popen(
            ["esphome", "compile", str(config)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except OSError as error:
        raise LintError(f"cannot run the ESPHome CLI: {error}") from error
    build: Path | None = None
    assert process.stdout is not None
    for line in process.stdout:
        sys.stdout.write(line)
        match = BUILD_PATH.search(line)
        if match:
            build = Path(match["path"])
    if process.wait() != 0:
        raise LintError(f"{config}: the compile failed, so there is no build to lint")
    if build is None:
        raise LintError(f"{config}: the compile printed no build path")
    return build


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="compile-lint",
        description="Report compiler warnings in this repository's code from ESPHome builds.",
    )
    parser.add_argument(
        "builds", nargs="*", type=Path, metavar="BUILD", help="an ESPHome build directory"
    )
    parser.add_argument(
        "--compile",
        type=Path,
        action="append",
        default=[],
        metavar="CONFIG",
        help="compile this config with the ESPHome CLI first, then lint its build, repeatable",
    )
    parser.add_argument(
        "--config-root",
        type=Path,
        default=Path.cwd(),
        help="the repository checkout the builds compiled, default the current directory",
    )
    parser.add_argument(
        "--flag",
        action="append",
        dest="flags",
        metavar="FLAG",
        help=f"an extra warning flag, repeatable, default {' '.join(DEFAULT_FLAGS)}",
    )
    parser.add_argument(
        "--annotate", action="store_true", help="also print GitHub workflow annotations"
    )
    parser.add_argument("--summary", type=Path, help="append a Markdown summary to this file")
    parser.add_argument(
        "--verbose", action="store_true", help="also list the diagnostics set aside as not owned"
    )
    args = parser.parse_args(argv)
    if not args.builds and not args.compile:
        parser.error("give a BUILD directory or a --compile CONFIG")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(os.path.normpath(args.config_root.resolve()))
    flags: list[str] = args.flags or DEFAULT_FLAGS
    owned = owned_sources(root)
    results: list[BuildResult] = []
    try:
        builds: list[Path] = [*args.builds, *(compile_config(c) for c in args.compile)]
        for build in builds:
            lint = BuildLint(Path(os.path.normpath(build.resolve())), root, flags, owned)
            results.append(lint.run())
    except LintError as error:
        print(f"compile-lint: {error}", file=sys.stderr)
        return 2
    for result in results:
        for finding in result.findings:
            print(
                f"{result.node}: {finding.path}:{finding.line}:{finding.column}: "
                f"{finding.severity}: {finding.message}"
            )
            if args.annotate:
                print(annotation(result.node, finding))
        print(
            f"{result.node}: {len(result.findings)} in this repository's code, "
            f"{len(result.ignored)} set aside as generated or third-party"
        )
        if args.verbose:
            for diagnostic in result.ignored:
                print(
                    f"  set aside: {diagnostic.path}:{diagnostic.line}:{diagnostic.column}: "
                    f"{diagnostic.message}"
                )
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as stream:
            stream.write(summary(results))
    return 1 if any(r.findings for r in results) else 0
