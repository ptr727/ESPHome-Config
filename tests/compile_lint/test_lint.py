"""Tests for the compile-time lint, run against constructed builds and a fake compiler."""

import json
import shlex
import sys
from pathlib import Path

import pytest

from compile_lint.lint import (
    BuildLint,
    Finding,
    YamlIndex,
    annotation,
    cpp_string,
    lambda_pattern,
    main,
    owned_sources,
    parse_diagnostics,
    replace_source,
    syntax_only_arguments,
    yaml_scalars,
)

# Stands in for the cross compiler, warning on each source line that holds a "2.5" double literal.
FAKE_COMPILER = """
import os
import sys
from pathlib import Path

if os.environ.get("FAKE_COMPILER_FAIL"):
    print("/framework/core.h:1:1: error: expected declaration", file=sys.stderr)
    raise SystemExit(1)

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
  - platform: template
    level: !lambda |-
      // returns the scaled level
      return y * 2.5;
    flag: !lambda return id(total);
    member: !lambda |-
      id(total).reset(2.5); // don't
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
    return BuildLint(build, root, [], {}, YamlIndex(root))


def set_main(build: Path, *lines: str) -> None:
    (build / "src" / "main.cpp").write_text("\n".join(lines))


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
    result = BuildLint(build, root, [], owned_sources(root), YamlIndex(root)).run()
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


def test_an_inlined_block_lambda_is_reported_on_its_code_line(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    set_main(
        build, directive(root, 9), "static void f(float y) {", "  call.set_level(y * 2.5);", "}"
    )
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 22)]


def test_inline_search_matches_whole_tokens_only(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    set_main(build, directive(root, 9), "  call.set_level(may * 2.5);")
    result = lint(root, build).run()
    assert result.findings == []


def test_an_id_only_lambda_is_not_searched_for(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    # The global's own declaration names it, and must not land on the flag lambda.
    set_main(build, directive(root, 9), "  total->set_initial(2.5);")
    result = lint(root, build).run()
    assert result.findings == []


def test_a_global_member_access_and_a_quoted_comment_match_the_generated_line(
    tmp_path: Path,
) -> None:
    root, build = write_build(tmp_path, "")
    set_main(build, directive(root, 25), "      total->value().reset(2.5);  ")
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 25)]


def test_code_after_a_remote_package_directive_is_set_aside(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    remote = f'      #line 5 "{tmp_path}/data/packages/remote.yaml"'
    set_main(build, directive(root, 12), "      return x * 2.5;", remote, "      return x * 2.5;")
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 11)]
    assert len(result.ignored) == 1


def test_a_command_string_database_with_a_compiler_cache_is_rechecked(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    set_main(build, "auto f = [](float x) {", directive(root, 12), "      return x * 2.5;", "});")
    compiler = tmp_path / "fake_compiler.py"
    command = (
        f"/usr/bin/ccache {shlex.quote(sys.executable)} {shlex.quote(str(compiler))} "
        "-include pch.h -o main.o -c src/main.cpp"
    )
    database = [{"directory": str(build), "file": "src/main.cpp", "command": command}]
    (build / "build" / "compile_commands.json").write_text(json.dumps(database))
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 11)]


def fake_esphome(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, output: str, status: int) -> None:
    """Put an esphome on PATH that prints the given compile output and exits with the status."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "esphome"
    script.write_text(f"#!{sys.executable}\nprint({output!r})\nraise SystemExit({status})\n")
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{Path(sys.executable).parent}")


def test_compile_mode_lints_the_build_path_the_compile_prints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, build = write_build(tmp_path, "int main() { return 0; }\n")
    fake_esphome(tmp_path, monkeypatch, f"INFO Compiling app... Build path: {build}", 0)
    status = main(["--config-root", str(root), "--compile", str(root / "test" / "device.yaml")])
    assert status == 0


def test_compile_mode_exits_two_when_the_compile_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = write_build(tmp_path, "")
    fake_esphome(tmp_path, monkeypatch, "ERROR Error while reading config", 1)
    status = main(["--config-root", str(root), "--compile", str(root / "test" / "device.yaml")])
    assert status == 2


def test_an_unreadable_yaml_file_is_a_failure_to_run(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    (root / "test" / "device.yaml").write_text("sensor: [unclosed\n")
    set_main(build, directive(root, 12), "      return x * 2.5;")
    assert main(["--config-root", str(root), str(build)]) == 2


def test_preload_skips_a_broken_file_the_build_does_not_use(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    (root / "test" / "scratch.yaml").write_text("sensor: [unclosed\n")
    set_main(build, "auto f = [](float x) {", directive(root, 12), "      return x * 2.5;", "});")
    index = YamlIndex(root)
    index.preload()
    result = BuildLint(build, root, [], {}, index).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 11)]


def test_an_inlined_block_lambda_behind_a_spanning_comment_lands_on_its_return(
    tmp_path: Path,
) -> None:
    root, build = write_build(tmp_path, "")
    with (root / "test" / "device.yaml").open("a") as stream:
        stream.write("    spanned: !lambda |-\n      /* scale\n      it */ return z * 2.5;\n")
    set_main(build, directive(root, 9), "  call.set_spanned(z * 2.5);")
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 28)]


def test_from_log_lints_the_last_build_path_a_compile_log_names(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "int main() { return 0; }\n")
    log = tmp_path / "compile.log"
    log.write_text(f"INFO Reading\nINFO Compiling app... Build path: {build}\nINFO Done\n")
    assert main(["--config-root", str(root), "--from-log", str(log)]) == 0


def test_from_log_without_a_build_path_is_a_failure_to_run(tmp_path: Path) -> None:
    root, _ = write_build(tmp_path, "")
    log = tmp_path / "compile.log"
    log.write_text("ERROR Error while reading config\n")
    assert main(["--config-root", str(root), "--from-log", str(log)]) == 2


def test_a_spanning_block_comment_in_a_line_lambda_keeps_later_lines_mapped(
    tmp_path: Path,
) -> None:
    root, build = write_build(tmp_path, "")
    with (root / "test" / "device.yaml").open("a") as stream:
        stream.write(
            "    commented: !lambda |-\n      /* two\n      lines */\n      w = w * 2.5;\n"
        )
    # ESPHome collapses the comment, so the code is the second emitted line, from YAML line 29.
    set_main(build, directive(root, 27), "         ", "      w = w * 2.5;")
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 29)]


def test_a_folded_lambda_is_one_logical_line(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    with (root / "test" / "device.yaml").open("a") as stream:
        stream.write("    folded: >-\n      return v\n      * 2.5;\n")
    set_main(build, directive(root, 27), "  call.set_folded(v * 2.5);")
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 27)]


def test_repo_code_after_a_remote_lambda_is_still_searched(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    remote = tmp_path / "data" / "packages" / "remote.yaml"
    remote.parent.mkdir(parents=True)
    remote.write_text("sensor:\n  - lambda: return q * 2.5;\n")
    line = f'      #line 3 "{remote}"'
    set_main(build, directive(root, 9), line, "      return q * 2.5;", "  call.set_level(y * 2.5);")
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 22)]
    assert len(result.ignored) == 1


def test_an_included_file_with_no_directive_is_searched(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    (root / "templates").mkdir()
    (root / "templates" / "extra.yaml").write_text("sensor:\n  - level: !lambda return u * 2.5;\n")
    with (root / "test" / "device.yaml").open("a") as stream:
        stream.write("packages:\n  extra: !include ../templates/extra.yaml\n")
    set_main(build, directive(root, 9), "  call.set_level(u * 2.5);")
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("templates/extra.yaml", 2)]


def test_the_build_config_read_from_the_compile_log_is_searched(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, build = write_build(tmp_path, "")
    # No #line names the config, so only the log can say this build came from it.
    set_main(build, "static void f(float y) {", "  call.set_level(y * 2.5);", "}")
    log = tmp_path / "compile.log"
    config = root / "test" / "device.yaml"
    log.write_text(
        f"INFO Reading configuration {config}...\nINFO Compiling app... Build path: {build}\n"
    )
    assert main(["--config-root", str(root), "--from-log", str(log)]) == 1
    assert "device-test: test/device.yaml:22:1: warning:" in capsys.readouterr().out


def test_an_args_entry_owns_only_the_diagnostic_inside_it(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    with (root / "test" / "device.yaml").open("a") as stream:
        stream.write(
            '    text:\n      format: "%.1f %.1f"\n'
            '      args: ["id(left).state * 2.5", id(right).state]\n'
        )
    set_main(
        build, directive(root, 9), '  str_sprintf("%.1f %.1f", left->state * 2.5,   right->state);'
    )
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 28)]


def test_a_recheck_failing_outside_owned_code_is_a_failure_to_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, build = write_build(tmp_path, "int main() { return 0; }\n")
    monkeypatch.setenv("FAKE_COMPILER_FAIL", "1")
    assert main(["--config-root", str(root), str(build)]) == 2


def test_a_bare_args_entry_is_attributed_at_its_column(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    with (root / "test" / "device.yaml").open("a") as stream:
        stream.write('    log:\n      format: "v %.1f"\n      args: [x2.5]\n')
    set_main(build, directive(root, 9), '  ESP_LOGD("main", "v %.1f", x2.5);')
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 28)]


def test_an_args_entry_matches_only_beside_its_own_format(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    with (root / "test" / "device.yaml").open("a") as stream:
        stream.write('    float_log:\n      format: "v %.1f\\n"\n      args: [x2.5]\n')
        stream.write('    bool_log:\n      format: "b %d"\n      args: [x2.5]\n')
    set_main(build, directive(root, 9), '  ESP_LOGD("main", "v %.1f\\012", x2.5);')
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 28)]


def test_cpp_string_matches_esphome_escaping() -> None:
    assert cpp_string('a "b"\n\\') == '"a \\042b\\042\\012\\134"'


def test_an_args_entry_beside_a_substituted_format_still_matches(tmp_path: Path) -> None:
    root, build = write_build(tmp_path, "")
    with (root / "test" / "device.yaml").open("a") as stream:
        stream.write('    named_log:\n      format: "${name} %.1f"\n      args: [x2.5]\n')
    set_main(build, directive(root, 9), '  ESP_LOGD("main", "kitchen %.1f", x2.5);')
    result = lint(root, build).run()
    assert [(f.path, f.line) for f in result.findings] == [("test/device.yaml", 28)]
