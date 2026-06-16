# Repository Guidelines

## Project Structure & Module Organization

PhaseSix is a Django 5 project. Project configuration lives in `phasesix/`.
Domain features are root-level Django apps such as `characters/`, `campaigns/`,
`worlds/`, `plots/`, and `rules/`. Keep models, views, URLs, migrations,
templates, and tests inside the app that owns the behavior.

Shared templates live in `templates/`; app-specific templates belong under
`<app>/templates/<app>/`. Source assets belong in each app's `static/`
directory; collected static files and uploads are stored in `static_files/` and
`media_files/`. German translations live in
`locale/de/LC_MESSAGES/`.

## Build, Test, and Development Commands

- `cp .env.example .env`: create local configuration; SQLite is used when
  `DATABASE_ENGINE` is unset.
- `uv sync --dev`: install Python 3.13 dependencies and development tools.
- `uv run manage.py migrate`: apply database migrations.
- `uv run manage.py runserver`: start the local Django server.
- `uv run manage.py test`: run the complete Django test suite.
- `uv run manage.py makemigrations --check --dry-run`: verify model changes have
  matching migrations.
- `git diff --relative --name-only --diff-filter=ACMR -- '*.py' | xargs -r -n1 env UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync black --fast --target-version py313`:
  format changed Python files. Keep `xargs -n1`; passing multiple files to Black
  can hang after formatting when its process pool shuts down in restricted
  automation environments. Ruff is not installed in this project.

## Coding Style & Naming Conventions

Use four spaces for Python and Black's default formatting. Use two spaces in
Django templates, matching the `djLint` configuration in `pyproject.toml`.
Follow Django conventions: `snake_case` for functions and fields, `PascalCase`
for classes, and descriptive URL names. Avoid coupling unrelated apps.

For UI work, prefer existing Bootstrap classes over custom CSS. Build modals
and sidebars through the `modals_sidebars` app. Put JavaScript in app static
files rather than templates, and favor `data-*` driven behavior.

## Atmospheric UI Style

Public-facing world, rules, and material pages use a dark-fantasy atmospheric
style. The same visual language also applies to character sheets, campaigns,
profiles, rulebook pages, the index page, fragments, modal content, and
sidebars. Reuse the shared components instead of creating unrelated Bootstrap
card or navigation variants.

- Use the `catalog-card` classes from
  `characters/static/theme/_catalog_cards.scss` for reusable content cards such
  as weapons, armor, spells, and character templates. Cards should have a
  framed visual header, an overlaid type and title, a readable body, and a
  compact metadata band.
- Use app-specific variants only when their content needs distinct behavior:
  `item-card` styles live in `_armory.scss`, `foe-card` styles in `_rules.scss`,
  and wiki article indexes in `_worlds.scss`.
- Use `atmospheric-navigation` on list-group navigation containers and
  `atmospheric-tabs` on tab or pill navigation. Modal and offcanvas shells are
  styled through `atmospheric-modal`. Preserve Bootstrap's `active`,
  `data-bs-toggle`, collapse, modal, sidebar, and HTMX/data-driven behavior.
- Apply atmospheric navigation styling consistently to `_navigation.html`
  fragments and navigation rendered inside modals. Keep the main site
  navigation comparatively restrained: do not add decorative `::before` or
  `::after` ornaments to its items.
- Prefer model artwork for visual headers. When no image exists, show a
  meaningful bundled Game Icon inside a `*-sigil` fallback instead of a generic
  placeholder image.
- Use Bootstrap theme variables so the style works for Tirakan and other
  worlds. Decorative borders, glows, sigils, active navigation, and metadata
  accents use `--bs-primary` and `--bs-primary-rgb`. Backgrounds and text use
  variables such as `--bs-tertiary-bg`, `--bs-body-bg`, and
  `--bs-secondary-color`; shadows and overlays use `--bs-black-rgb` and
  `--bs-white-rgb`.
- Reserve semantic colors for their meaning: use danger for destructive or
  harmful states, warning for cautions or magical/special states, success for
  positive states, and other Bootstrap semantic colors where appropriate. Do
  not use danger as the default decorative accent or hard-code a world-specific
  palette.
- Keep descriptions readable below imagery; do not place substantial text or
  interactive controls over images. Maintain responsive one-column behavior on
  small screens.
- Use bundled Font Awesome 5 names (`fas`, `far`) and verify new Game Icon
  classes exist locally. Preserve accessible labels and mark decorative icons
  with `aria-hidden="true"` where appropriate.
- Put shared SCSS partials under `characters/static/theme/` and import them from
  `generic.scss`. Do not add template-local `<style>` blocks.

### Brand Themes

The default PhaseSix brand is served when no world matches the request domain.
`worlds/middleware.py` selects configured world brands, including Tirakan and
Nexus, from their database-backed domain names. Shared atmospheric components
must work for all three brands, while each theme entrypoint may add restrained
brand-specific overrides.

- Treat `characters/static/theme/phasesix.scss`,
  `characters/static/theme/nexus.scss`, and
  `characters/static/theme/tirakan.scss` as the source of truth for each
  brand's Bootstrap palette and brand-specific presentation. Use Bootstrap CSS
  variables in shared partials so changing a theme palette updates all
  atmospheric elements.
- Keep PhaseSix clean, polished, and system-neutral. It is the common toolkit
  for every RPG setting, using clear blue accents, cool navy-gray surfaces,
  ordinary sans-serif typography, softer corners, and subtle layered panels.
  Avoid setting-specific fantasy or science-fiction decoration.
- Keep Nexus futuristic and alien. Use its Oxanium headings, cyan/teal base,
  purple accents, sharp geometry, and atmospheric glow to distinguish it from
  the neutral PhaseSix toolkit.
- Keep Tirakan warm but subdued: use a near-black neutral background,
  charcoal foreground panels, muted ember-gold primary accents, and restrained
  secondary colors. Avoid saturated orange embers and broadly brown-tinted
  panels.
- Put Tirakan-only presentation overrides in
  `characters/static/theme/_tirakan_brand.scss`. Do not hard-code Tirakan
  colors into shared component partials.
- Tirakan ornaments should be slim, lightly curved linework derived from the
  primary color. Keep them subtle and sparse; avoid thick corner blocks,
  oversized glyphs, or playful flourishes that compete with content.
- Tirakan offcanvas sidebars must prioritize readability over translucency.
  Use a mostly opaque `--bs-body-bg-rgb` surface, a small amount of restrained
  primary tint, and a light backdrop blur. Keep this treatment Tirakan-only
  unless the other brand explicitly needs it.
- Each theme entrypoint contains a `Theme build marker` comment. Whenever any
  imported SCSS partial or theme-specific SCSS changes, update that marker in
  all three entrypoints. This changes their source timestamps/content so
  `collectstatic` recompiles every theme instead of serving stale generated
  CSS.

After UI style changes, compile all three active themes:

- `uv run python -c "import sass; sass.compile(filename='characters/static/theme/tirakan.scss', include_paths=['characters/static/theme'])"`
- `uv run python -c "import sass; sass.compile(filename='characters/static/theme/phasesix.scss', include_paths=['characters/static/theme'])"`
- `uv run python -c "import sass; sass.compile(filename='characters/static/theme/nexus.scss', include_paths=['characters/static/theme'])"`

## Testing Guidelines

Tests use Django's test runner and are currently organized as `<app>/tests.py`.
Name test methods `test_<expected_behavior>` and use Django `TestCase` or the
closest existing local pattern. Add focused regression tests for changed views,
models, permissions, and campaign/world scoping. Run the affected app tests,
then the full suite before opening a pull request.

## Commit & Pull Request Guidelines

Recent commits use short, imperative summaries such as `Added all npc sidebar
to campaign page`. Keep each commit focused and explain the user-visible intent.

Pull requests should include a concise description, testing performed, linked
issues when applicable, and screenshots for template or UI changes. Include
generated migrations with model changes. Never commit secrets from `.env`,
local uploads in `media_files/`, caches, or database dumps.

## Agent-Specific Instructions

Automation agents may edit and test the working tree, but must not create
commits or pull requests unless explicitly requested.
