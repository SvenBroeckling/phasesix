# Repository Guidelines

## Project Structure & Module Organization
- Django project root lives here; `manage.py` is the entry point and `phasesix/` contains settings and core configuration.
- Feature modules are Django apps at the top level (for example: `characters/`, `campaigns/`, `rules/`, `portal/`, `api/`).
- Templates are centralized in `templates/` with additional app-level templates alongside their apps.
- Static assets live in `static/` folders in the apps and app-specific assets (such as `characters/static/`). Uploaded/media files are in `media_files/`.
- Prever bootstrap classes over css, do not create custom css if possible
- Data and utilities are in `contrib/` and project artifacts like `phasesix.sql.bz2` are stored at the repo root.
- Don't add javascript to html files, create static files or use data- attribute driven mechanics as much as possible. 


## Build, Test, and Development Commands
- `uv run manage.py runserver` — run the local development server.
- `uv run manage.py test` — run Django’s test runner across apps.
- `uv run manage.py makemigrations <app>` — create migrations when models change.
- `uv run manage.py migrate` — apply database migrations.

## Modals, Sidebars, Bootstrap
- Use the `modals_sidebars` django app in this project to create modals and sidebars

## Coding Style & Naming Conventions
- Python: 4-space indentation, follow Django conventions for models, views, and templates.
- App/module naming follows `lower_snake_case` (for example: `body_modifications/`).
- Templates and static assets follow Django defaults: `templates/<app>/...`, `static/<app>/...`.
- No repo-wide formatter or linter config is present; match surrounding style when editing.

## Testing Guidelines
- There are no configured tests in this application

## Commit & Pull Request Guidelines
- do not commit changes
- do not make pull requests

## Configuration & Data
- Ensure required environment variables and local settings are configured in your Django setup before running the server.
- Treat `phasesix.sql.bz2` as data backup/reference; do not edit it directly in PRs.
