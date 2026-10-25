"""Run the lint as `python3 -m compile_lint`, the form the ESPHome image runs it in."""

from compile_lint.lint import main

raise SystemExit(main())
