# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`dtool-lookup-gui` is a GTK 3 / PyGObject desktop application (entry point `dtool-gui`)
for browsing and managing [dtool](https://github.com/jic-dtool/dtool) datasets and for
querying a [dtool-lookup-server](https://github.com/jic-dtool/dtool-lookup-server) and its
mongo / dependency-graph plugins. It talks to servers through `dtool_lookup_api` and to
local/remote (S3, SMB) storage through `dtoolcore`.

## Setup, build, run

The app cannot start until the GSettings schema is compiled. After `pip install -e .[test]`,
run `glib-compile-schemas .` from **inside** `dtool_lookup_gui/` (produces
`dtool_lookup_gui/gschemas.compiled`). Without it, launch fails with a
`g-file-error-quark ... gschemas.compiled ... No such file` error. The custom build backend
(`maintenance/custom_build_backend.py`) does this automatically for `build_wheel`/`build_sdist`,
but an editable install does not — so do it by hand during development.

- Run the app: `dtool-gui` (under Wayland use `GDK_BACKEND=x11 dtool-gui`).
- Version comes from `setuptools_scm`, written to `dtool_lookup_gui/version.py`.
- System deps: GTK 3 + GtkSourceView 4 (e.g. `gir1.2-gtksource-4`) plus the GObject-introspection
  build packages — see `README.rst` and `.github/workflows/build-on-*.yml` for the exact
  per-platform list.

## Tests

- Run all: `pytest` (config in `pyproject.toml`; collects coverage into an HTML report).
- Single test: `pytest test/test_main_window_actions.py::test_do_search`.
- Headless run needs an X server: `xvfb-run --auto-servernum pytest`. CI additionally
  parallelizes with `pytest-xdist` (`-n`) under `tini` to reap zombie xdist workers.

`test/conftest.py` is the heart of the test harness and worth reading before writing tests:

- It sets `DBUS_SESSION_BUS_ADDRESS=/dev/null` and `GSETTINGS_BACKEND=memory` at import time
  so each test process gets isolated settings and so multiple `Gio.Application` instances don't
  collide on the exported D-Bus object path. Do not undo these.
- `dtool_lookup_api` is fully mocked (patched at the `LookupClient` base classes) to return
  fixture JSON from `test/data/`. Tests never reach a real server.
- `asyncio` and the GTK main loop share one event loop via `gbulb` / `GLibEventLoopPolicy`
  (a `CustomGLibEventLoopPolicy` in conftest). This is also how `main.run_gui` wires things.

## Architecture

The codebase follows an MVC-ish split, organized around **Gio.Actions** rather than direct
signal callbacks.

- `dtool_lookup_gui/main.py` — the `Gtk.Application` subclass: startup/activation lifecycle
  (`do_startup`, `do_activate`, `do_command_line`), app-level actions (config import/export,
  token renewal, logging), and custom GObject signals (`dtool-config-changed`, `token-renewed`,
  `startup-done`, `activation-done`). `run_gui()` is the `dtool-gui` entry point.
- `views/` — one `.py` + matching `.ui` (GtkBuilder XML) per window/dialog. `MainWindow`
  (`views/main_window.py`) is the largest and hosts most window-level actions. UI classes use
  the `@Gtk.Template(filename=...'.ui')` decorator.
- `widgets/` — custom GTK widgets (list boxes, rows, popovers, graph rendering). These must be
  imported in `main.py` purely to register their types with the GObject type system before the
  `.ui` files referencing them are loaded — keep those imports.
- `models/` — data layer wrapping `dtoolcore` / the lookup API: `DatasetModel`, the `BaseURI`
  hierarchy (`LocalBaseURIModel`, `S3BaseURIModel`, `SMBBaseURIModel`, `LookupBaseURIModel`),
  `SearchState`, `Settings`, and graph models.
- `utils/` — async subprocess/multiprocessing helpers, copy manager, dependency-graph layout,
  query parsing, logging.

### Actions are the unit of behavior (read CONTRIBUTING.md)

New behavior should be wrapped in atomic `Gio.SimpleAction`s, not ad-hoc signal handlers, so it
can be triggered from the GUI, CLI, shortcuts, or tests. Conventions enforced in this repo:

- Handler methods are named `do_<action>` (e.g. `do_search`) and attached to the app or the
  window the action belongs to. Actions are created with `Gio.SimpleAction.new("name", param_type)`
  and registered with `self.add_action(...)` (see the block in `MainWindow`).
- Actions taking parameters use `GLib.Variant` parameter types (row index, URI string, etc.).
- Write at least one unit test per action. The pattern is two tests: one calls `app.do_<action>(...)`
  directly against mock data; the other activates it through the framework
  (`app.activate_action('<action-name>')`) and asserts that mocked internals were invoked.

## Conventions

- Follow PEP 8 (line-length is the allowed exception).
- Branch names are prefixed with creation date, e.g. `2023-04-06-pagination`.
- Prefix commit messages with a type tag: `BUG`, `CI`, `DEP`, `DOC`, `ENH`, `MAINT`, `TST`, `WIP`.
- Editing `.ui` files: the app uses custom widgets, so point Glade at `glade/catalog`
  (Preferences → Extra Catalog & Template paths).
- Packaging for releases is done with PyInstaller under `pyinstaller/` (per-platform `MANIFEST.*`
  and spec files); CI lives in `.github/workflows/`.
