"""Report compiler warnings that land in this repository's own code from an ESPHome build.

A lambda only compiles inside the generated main.cpp, so the lint reads the build ESPHome produced.
It reruns the compile of main.cpp, and of any translation unit this repository authored.
The rerun is syntax-only, with the build's own flags plus a stricter warning.
It keeps the diagnostics in this repository's code and sets aside the rest.

A diagnostic is this repository's when it lands in one of these places:
  - a line of a YAML lambda, which ESPHome copies into main.cpp after a #line directive
  - a lambda ESPHome inlined as a bare expression, found by searching the YAML for it
  - a C/C++ file under the config root, or a copy of one in the build tree, matched by content

Run it on any route that runs the ESPHome CLI, shown here in the container with the tree at /config.
It either compiles a config first or reads a build already compiled:
  PYTHONPATH=/config/tools/compile-lint/src python3 -m compile_lint --config-root /config \\
    --compile /config/test/<template>.yaml
  PYTHONPATH=/config/tools/compile-lint/src python3 -m compile_lint --config-root /config \\
    /cache/build/<node>

Exit status is 0 when nothing was found, and 1 when a warning or error landed in owned code.
It is 2 when the lint could not run, such as after a failed compile or without a compile database.
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

# Stricter than the build's own warning set, and limited to warnings a YAML author can fix.
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
# - An id(name) before a member access, which becomes name-> on a component.
# - On a global, that id(name) becomes name->value() and keeps its dot.
# - A bare id(name), which becomes name, or name->value() for a global.
REWRITE = re.compile(
    r"(?P<substitution>\$\{[^}]*\}|\$[A-Za-z_]\w*)"
    r"|\bid\(\s*(?P<member>[\w${}]+)\s*\)\."
    r"|\bid\(\s*(?P<bare>[\w${}]+)\s*\)"
)
# ESPHome's own comment remover, which turns a comment into a space and keeps string literals.
COMMENT = re.compile(
    r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"', re.DOTALL | re.MULTILINE
)
ID_REFERENCE = re.compile(r"\bid\(\s*([\w${}]+)\s*\)")
RETURN_EXPRESSION = re.compile(r"^return\s+(?P<expression>[^;]+);?$")
BARE_TOKEN = re.compile(r"^[\w.]+$")
YAML_PATH = re.compile(r"^[\w./-]+\.ya?ml$")
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
    """A YAML scalar's 1-based line span, its text, and its lines as ESPHome emits them.

    Each emitted line pairs the YAML line its code sits on with its text after comment removal.
    """

    start: int
    end: int
    text: str
    lines: tuple[tuple[int, str], ...]


@dataclass(frozen=True)
class Directive:
    """A #line directive in main.cpp: its own 0-based index, and the YAML line it names.

    The path is None for a file outside the config root, such as a remote package's YAML.
    """

    index: int
    line: int
    path: str | None
    absolute: Path


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


def is_main_path(path: Path) -> bool:
    """Say whether a path is the generated main.cpp."""
    return path.name == "main.cpp" and path.parent.name == "src"


def is_main(entry: dict[str, Any]) -> bool:
    """Say whether an entry compiles the generated main.cpp."""
    return is_main_path(entry_path(entry))


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


def emitted_lines(text: str, first: int) -> tuple[tuple[int, str], ...]:
    """Split lambda text into the lines ESPHome emits, each with the YAML line its code sits on.

    ESPHome removes comments from the whole lambda, so a block comment spanning lines joins them.
    """
    chars: list[tuple[str, int]] = []
    line = first
    position = 0

    def keep(chunk: str) -> None:
        nonlocal line
        for char in chunk:
            chars.append((char, line))
            line += char == "\n"

    for match in COMMENT.finditer(text):
        keep(text[position : match.start()])
        if match[0].startswith("/"):
            chars.append((" ", line))
            line += match[0].count("\n")
        else:
            keep(match[0])
        position = match.end()
    keep(text[position:])
    lines: list[tuple[int, str]] = []
    current: list[tuple[str, int]] = []
    for char, source in [*chars, ("\n", line)]:
        if char != "\n":
            current.append((char, source))
            continue
        code = [source for char, source in current if not char.isspace()]
        lines.append((code[0] if code else source, "".join(char for char, _ in current)))
        current = []
    return tuple(lines)


def yaml_scalars(path: Path) -> list[Scalar]:
    """Return every scalar in a YAML file with its line span, tags and all left unresolved."""
    scalars: list[Scalar] = []

    def walk(node: yaml.Node) -> None:
        if isinstance(node, yaml.ScalarNode):
            start = node.start_mark.line + 1
            end = max(start, node.end_mark.line + (1 if node.end_mark.column > 0 else 0))
            text = str(node.value)
            if node.style == "|":
                # A literal block keeps its lines, and its body starts below the indicator.
                lines = emitted_lines(text, start + 1)
            else:
                # Any other style folds to one logical line, on the indicator's next line for >.
                first = start + 1 if node.style == ">" else start
                lines = ((first, " ".join(text for _, text in emitted_lines(text, first))),)
            scalars.append(Scalar(start, end, text, lines))
        elif isinstance(node, yaml.SequenceNode):
            for child in cast(list[yaml.Node], node.value):
                walk(child)
        elif isinstance(node, yaml.MappingNode):
            for key, value in cast(list[tuple[yaml.Node, yaml.Node]], node.value):
                walk(key)
                walk(value)

    # Composing builds nodes without constructing values, so ESPHome's tags need no constructor.
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
    """Caches each YAML file's scalars, read on first use or all at once."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._scalars: dict[Path, list[Scalar]] = {}

    def scalars(self, relative: str) -> list[Scalar]:
        """Return a repository file's scalars, failing the run where it does not parse."""
        try:
            return self.scalars_at(self.root / relative)
        except (OSError, yaml.YAMLError) as error:
            raise LintError(f"cannot read {relative}: {error}") from error

    def scalars_at(self, path: Path) -> list[Scalar]:
        """Return any file's scalars, such as a remote package's in the build cache."""
        if path not in self._scalars:
            self._scalars[path] = yaml_scalars(path)
        return self._scalars[path]

    def includes(self, relative: str) -> Iterator[str]:
        """Yield the repository YAML files a file names by relative path, as !include or file:."""
        directory = (self.root / relative).parent
        for scalar in self.scalars(relative):
            if YAML_PATH.match(scalar.text) and not scalar.text.startswith("/"):
                target = Path(os.path.normpath(directory / scalar.text))
                included = relative_to_root(target, self.root)
                if included is not None and target.is_file():
                    yield included

    def preload(self) -> None:
        """Read every YAML file now, so a later edit cannot shift lines against a build."""
        for path in walk_files(self.root, {".yaml", ".yml"}):
            # A file that does not parse fails the run only if a build turns out to need it.
            try:
                self.scalars(path.relative_to(self.root).as_posix())
            except LintError:
                continue


def normalize(text: str) -> str:
    """Collapse whitespace, so text matches however the generator spaced it."""
    return " ".join(text.split())


def strip_comments(text: str) -> str:
    """Remove comments the way ESPHome does before it emits a lambda."""
    return COMMENT.sub(lambda m: " " if m[0].startswith("/") else m[0], text)


def lambda_pattern(text: str) -> re.Pattern[str]:
    """Return a pattern for YAML lambda text that matches the C++ ESPHome generates from it."""
    pieces: list[str] = []
    position = 0
    text = normalize(strip_comments(text))
    for match in REWRITE.finditer(text):
        pieces.append(re.escape(text[position : match.start()]))
        if match["substitution"]:
            pieces.append(".+?")
        elif match["member"]:
            pieces.append(lambda_pattern(match["member"]).pattern + r"(?:->|->value\(\)\.)")
        else:
            pieces.append(lambda_pattern(match["bare"]).pattern + r"(?:->value\(\))?")
        position = match.end()
    pieces.append(re.escape(text[position:]))
    return re.compile("".join(pieces))


def lambda_line(scalar: Scalar, directive: Directive, offset: int) -> tuple[int, str] | None:
    """Return the YAML line and text a generated line copies, offset lines after a directive.

    ESPHome numbers a lambda's #line one past the scalar's first line, which anchors the scalar.
    """
    if scalar.start + 1 != directive.line or offset >= len(scalar.lines):
        return None
    return scalar.lines[offset]


def inline_expressions(scalars: list[Scalar]) -> Iterator[tuple[int, re.Pattern[str]]]:
    """Yield the YAML line and pattern of each lambda ESPHome may inline as a bare expression."""
    for scalar in scalars:
        match = RETURN_EXPRESSION.match(normalize(" ".join(text for _, text in scalar.lines)))
        if not match:
            continue
        expression = match["expression"].strip()
        # A bare name or number would match any generated line that mentions it.
        if BARE_TOKEN.match(ID_REFERENCE.sub(r"\1", expression)):
            continue
        returns = (line for line, text in scalar.lines if text.strip().startswith("return"))
        line = next(returns, scalar.lines[0][0])
        pattern = lambda_pattern(expression).pattern
        yield line, re.compile(rf"(?<![\w.]){pattern}(?!\w)")


class BuildLint:
    """Lints one ESPHome build directory against the repository at the config root."""

    def __init__(
        self, build: Path, root: Path, flags: list[str], owned: dict[str, str], index: YamlIndex
    ) -> None:
        self.build = build
        self.root = root
        self.flags = flags
        self.owned = owned
        self.index = index
        self.main_lines: list[str] = []
        self.directives: list[Directive] = []
        self.failed: list[str] = []

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
            owned_error = False
            for diagnostic in diagnostics:
                findings = list(self.classify(diagnostic, Path(str(entry["directory"]))))
                if not findings:
                    result.ignored.append(diagnostic)
                owned_error |= any(f.severity == "error" for f in findings)
                for finding in findings:
                    if finding not in seen:
                        seen.add(finding)
                        result.findings.append(finding)
            if str(entry["file"]) in self.failed and not owned_error:
                # The build compiled, so an error outside owned code means the recheck itself broke.
                raise LintError(
                    f"{self.build.name}: the syntax-only compile of {entry['file']} failed"
                )
        result.findings.sort()
        return result

    def compile_main(self, entry: dict[str, Any]) -> list[Diagnostic]:
        """Compile main.cpp with its #line directives blanked, so diagnostics keep its lines.

        ESPHome never resets #line after a lambda or an LVGL widget.
        With the directives in place, generated code after one is reported against the wrong YAML.
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
            if match:
                absolute = Path(os.path.normpath(match["path"]))
                self.directives.append(Directive(index, int(match["line"]), relative, absolute))
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
        if completed.returncode != 0:
            self.failed.append(str(entry["file"]))
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
        if is_main_path(path) and self.main_lines:
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
            if directive.path is None:
                if self.copies_remote(directive, index, generated):
                    return
            else:
                for scalar in self.index.scalars(directive.path):
                    located = lambda_line(scalar, directive, index - directive.index - 1)
                    if located is None:
                        continue
                    line, text = located
                    if lambda_pattern(text).fullmatch(generated):
                        # The generated column counts ESPHome's indentation, not the YAML's.
                        yield Finding(
                            directive.path, line, 1, diagnostic.severity, diagnostic.message
                        )
                        return
        yield from self.match_inline(diagnostic, generated)

    def node_files(self) -> list[str]:
        """Return the build's repository YAML: its config, the files #line names, and includes."""
        pending = [d.path for d in self.directives if d.path is not None]
        pending += self.config_files()
        found: dict[str, None] = {}
        while pending:
            relative = pending.pop()
            if relative not in found:
                found[relative] = None
                pending.extend(self.index.includes(relative))
        return list(found)

    def config_files(self) -> list[str]:
        """Return the repository config a build came from, read from ESPHome's storage file."""
        data = Path(os.environ.get("ESPHOME_DATA_DIR", self.root / ".esphome"))
        names: list[str] = []
        for storage in sorted((data / "storage").glob("*.json")):
            try:
                build_path = json.loads(storage.read_text(encoding="utf-8")).get("build_path")
            except (OSError, ValueError, AttributeError):
                continue
            if build_path and Path(os.path.normpath(build_path)) == self.build:
                names.append(storage.name.removesuffix(".json"))
        return [
            p.relative_to(self.root).as_posix()
            for p in walk_files(self.root, {".yaml", ".yml"})
            if p.name in names
        ]

    def copies_remote(self, directive: Directive, index: int, generated: str) -> bool:
        """Say whether a generated line copies a lambda line of a remote package's YAML."""
        try:
            scalars = self.index.scalars_at(directive.absolute)
        except (OSError, yaml.YAMLError):
            # A remote file the build cache no longer holds cannot be told apart, so set it aside.
            return True
        for scalar in scalars:
            located = lambda_line(scalar, directive, index - directive.index - 1)
            if located is not None and lambda_pattern(located[1]).fullmatch(generated):
                return True
        return False

    def match_inline(self, diagnostic: Diagnostic, generated: str) -> Iterator[Finding]:
        """Attribute a diagnostic to the build's YAML lambdas whose expression was inlined there."""
        for relative in self.node_files():
            for line, pattern in inline_expressions(self.index.scalars(relative)):
                if pattern.search(generated):
                    yield Finding(relative, line, 1, diagnostic.severity, diagnostic.message)


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


def build_from_log(log: Path) -> Path:
    """Return the last build path a saved ESPHome compile log printed."""
    try:
        matches = BUILD_PATH.findall(log.read_text(encoding="utf-8", errors="replace"))
    except OSError as error:
        raise LintError(f"cannot read the compile log {log}: {error}") from error
    if not matches:
        raise LintError(f"{log}: the compile log holds no build path")
    return Path(matches[-1])


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
        "--from-log",
        type=Path,
        action="append",
        default=[],
        metavar="LOG",
        help="lint the build a saved ESPHome compile log names, repeatable",
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
    if not args.builds and not args.compile and not args.from_log:
        parser.error("give a BUILD directory, a --compile CONFIG, or a --from-log LOG")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(os.path.normpath(args.config_root.resolve()))
    flags: list[str] = args.flags or DEFAULT_FLAGS
    owned = owned_sources(root)
    index = YamlIndex(root)
    results: list[BuildResult] = []
    try:
        if args.compile:
            # The compile takes minutes, and an editor save during it would shift YAML lines.
            index.preload()
        builds: list[Path] = [*args.builds, *(build_from_log(log) for log in args.from_log)]
        builds += [compile_config(c) for c in args.compile]
        for build in builds:
            build = Path(os.path.normpath(build.resolve()))
            results.append(BuildLint(build, root, flags, owned, index).run())
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
