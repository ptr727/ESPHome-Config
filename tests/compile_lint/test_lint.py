"""Tests for the compile-time lint, run against constructed builds and a fake compiler."""

import json
import sys
from pathlib import Path

import pytest

from compile_lint.lint import (
    BuildLint,
    Finding,
    annotation,
    lambda_pattern,
    main,
    owned_sources,
    parse_diagnostics,
    replace_source,
    syntax_only_arguments,
    yaml_scalars,
)

# Stands in for the cross compiler: warns on every line of each source it reads that holds
# "2.5", as -Wdouble-promotion would on a double literal, naming the file the way gcc does.
FAKE_COMPILER = """
import sys
from pathlib import Path

for argument in sys.argv[1:]:
    path = Path(argument)
    if path.suffix in {".cpp", ".h"} and path.is_file():
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            column = line.find("2.5")
            if column >= 0:
                print(
                    f"{path}:{number}:{column + 1}: warning: implicit conversion from 'float' "
                    "to 'double' [-Wdouble-promotion]",
                    file=sys.stderr,
                )
                print(f"{path}:{number}:{column + 1}: note: context", file=sys.stderr)
"""

DEVICE_YAML = """\
substitutions:
  scale: "2.5"

globals:
  - id: total
    type: float

sensor:
  - platform: template
    filters:
      - lambda: return x * 2.5;
    on_value:
      - lambda: |-
          // Scales the running total.
          id(total) = id(total) * ${scale};
          id(relay).turn_on();
  - platform: template
    brightness: !lambda return x / 2.5f;
"""


def write_build(tmp_path: Path, main_cpp: str, header: str | None = None) -> tuple[Path, Path]:
    """Build a config root and an ESPHome-shaped build tree that the fake compiler compiles."""
    root = tmp_path / "config"
    (root / "test").mkdir(parents=True)
    (root / "test" / "device.yaml").write_text(DEVICE_YAML)
    build = tmp_path / "build" / "device-test"
    (build / "src").mkdir(parents=True)
    (build / "src" / "main.cpp").write_text(main_cpp)
    if header is not None:
        component = root / "components" / "widget"
        component.mkdir(parents=True)
        (component / "widget.h").write_text(header)
        copy = build / "src" / "esphome" / "components" / "widget"
        copy.mkdir(parents=True)
        (copy / "widget.h").write_text(header)
    compiler = tmp_path / "fake_compiler.py"
    compiler.write_text(FAKE_COMPILER)
    arguments = [sys.executable, str(compiler), "-Wall", "-o", "main.o", "-c", "src/main.cpp"]
    if header is not None:
        arguments.append(str(build / "src" / "esphome" / "components" / "widget" / "widget.h"))
    database = [{"directory": str(build), "file": "src/main.cpp", "arguments": arguments}]
    (build / "build").mkdir()
    (build / "build" / "compile_commands.json").write_text(json.dumps(database))
    return root, build


def lint(root: Path, build: Path) -> BuildLint:
    return BuildLint(build, root, [], {})


def directive(root: Path, line: int) -> str:
    return f'      #line {line} "{root}/test/../test/device.yaml"'


def test_parse_diagnostics_keeps_warnings_and_errors_and_skips_notes() -> None:
    text = """\
a.cpp:3:7: warning: unused [-Wunused]
a.cpp:3:7: note: declared here
b.h:10:1: error: expected ';'
In file included from a.cpp:1:
"""
    found = parse_diagnostics(text)
    assert [(d.path, d.line, d.severity) for d in found] == [
        ("a.cpp", 3, "warning"),
        ("b.h", 10, "error"),
    ]


def test_syntax_only_arguments_drop_outputs_and_add_flags() -> None:
    arguments = [
        "g++",
        "-o",
        "x.o",
        "-c",
        "-MD",
        "-MF",
        "x.d",
        "-fdiagnostics-color=always",
        "x.cpp",
    ]
    rebuilt = syntax_only_arguments(arguments, ["-Wdouble-promotion"])
    assert rebuilt[:2] == ["g++", "x.cpp"]
    assert "-o" not in rebuilt and "-MF" not in rebuilt and "-c" not in rebuilt
    assert "-fdiagnostics-color=always" not in rebuilt
    assert rebuilt[-1] == "-Wdouble-promotion"
    assert "-fsyntax-only" in rebuilt


def test_syntax_only_arguments_drop_a_compiler_cache_wrapper() -> None:
    rebuilt = syntax_only_arguments(["/usr/bin/ccache", "g++", "-c", "x.cpp"], [])
    assert rebuilt[:2] == ["g++", "x.cpp"]


def test_replace_source_keeps_the_original_directory_for_quoted_includes(tmp_path: Path) -> None:
    entry = {"directory": str(tmp_path), "file": "src/main.cpp"}
    replaced = replace_source(
        ["g++", "-I", "inc", "src/main.cpp"], entry, Path("/scratch/main.cpp")
    )
    assert replaced == ["g++", "-I", "inc", "/scratch/main.cpp", "-iquote", str(tmp_path / "src")]


def test_lambda_pattern_applies_esphome_rewrites() -> None:
    pattern = lambda_pattern("id(total) = id(sensor_${n}).state * ${scale};")
    assert pattern.fullmatch("total->value() = sensor_1->state * 2.5;")
    assert pattern.fullmatch("total = sensor_abc->state * 3;")
    assert not pattern.fullmatch("other = sensor_1->state * 2.5;")


def test_yaml_scalars_give_block_and_inline_spans_with_tags_unresolved(tmp_path: Path) -> None:
    path = tmp_path / "device.yaml"
    path.write_text(DEVICE_YAML)
    scalars = {s.text: (s.start, s.end) for s in yaml_scalars(path)}
    assert scalars["return x * 2.5;"] == (11, 11)
    assert scalars["return x / 2.5f;"] == (18, 18)
    block = next(text for text in scalars if text.startswith("// Scales"))
    assert scalars[block] == (13, 16)


def test_block_lambda_line_is_found_past_a_blanked_comment(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    main_cpp = "\n".join(
        [
            "void setup() {",
            directive(root, 14),
            "      ",
            "      total->value() = total->value() * 2.5;",
            "      relay->turn_on();",
            "}",
        ]
    )
    (build / "src" / "main.cpp").write_text(main_cpp)
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 15)]


def test_inline_lambda_is_reported_on_its_own_line(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    main_cpp = "\n".join(
        ["auto f = [](float x) {", directive(root, 12), "      return x * 2.5;", "});"]
    )
    (build / "src" / "main.cpp").write_text(main_cpp)
    result = lint(root, build).run()
    assert [(f.path, f.line, f.column) for f in result.findings] == [("test/device.yaml", 11, 1)]


def test_generated_code_after_a_directive_is_set_aside(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    # A directive ESPHome emits for an LVGL widget, followed by code no YAML line holds.
    main_cpp = "\n".join([directive(root, 9), "  widget_set_zoom(w, 2.5);", "  other(2.5);"])
    (build / "src" / "main.cpp").write_text(main_cpp)
    result = lint(root, build).run()
    assert result.findings == []
    assert len(result.ignored) == 2


def test_an_inlined_expression_is_found_by_searching_the_yaml(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    main_cpp = "\n".join(
        [directive(root, 9), "static void f(float x) {", "  call.set_brightness(x / 2.5f);", "}"]
    )
    (build / "src" / "main.cpp").write_text(main_cpp)
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 18)]


def test_a_component_header_copied_into_the_build_maps_to_the_repository(tmp_path: Path) -> None:
    header = "inline double scale(float v) { return v * 2.5; }\n"
    root, build = write_build(tmp_path, "int main() {}\n", header=header)
    result = BuildLint(build, root, [], owned_sources(root)).run()
    assert [(f.path, f.line) for f in result.findings] == [("components/widget/widget.h", 1)]


def test_main_exit_status_is_one_with_findings_and_writes_the_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, build = write_build(tmp_path, "")
    main_cpp = "\n".join(
        ["auto f = [](float x) {", directive(root, 12), "      return x * 2.5;", "});"]
    )
    (build / "src" / "main.cpp").write_text(main_cpp)
    summary = tmp_path / "summary.md"
    status = main(["--config-root", str(root), "--annotate", "--summary", str(summary), str(build)])
    assert status == 1
    out = capsys.readouterr().out
    assert "device-test: test/device.yaml:11:1: warning:" in out
    assert "::warning file=test/device.yaml,line=11,col=1," in out
    assert "| `device-test` | `test/device.yaml:11:1` |" in summary.read_text()


def test_main_exit_status_is_zero_when_clean(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "int main() { return 0; }\n")
    assert main(["--config-root", str(root), str(build)]) == 0


def test_main_exit_status_is_two_without_a_compile_database(tmp_path: Path) -> None:
    (tmp_path / "build").mkdir()
    assert main(["--config-root", str(tmp_path), str(tmp_path / "build")]) == 2


def test_help_exits_zero_and_unknown_arguments_are_refused(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as helped:
        main(["--help"])
    assert helped.value.code == 0
    assert capsys.readouterr().out.startswith("usage: compile-lint")
    with pytest.raises(SystemExit) as refused:
        main(["--bogus", "build"])
    assert refused.value.code != 0
    assert "unrecognized arguments: --bogus" in capsys.readouterr().err


def test_annotation_escapes_workflow_command_characters() -> None:
    finding = Finding("test/a,b.yaml", 3, 1, "warning", "50% off\nnext")
    assert annotation("node:x", finding) == (
        "::warning file=test/a%2Cb.yaml,line=3,col=1,title=compile-lint node%3Ax::50%25 off%0Anext"
    )
