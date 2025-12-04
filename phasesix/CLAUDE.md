# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Phase Six is a Django-based pen & paper roleplay platform powering [Phase Six](https://phasesix.org/) and [Realms of Tirakan](https://tirakans-reiche.de/). It's a multi-tenant RPG platform with character creation, campaigns, homebrew content, and PDF generation capabilities.

## Common Development Commands

### Initial Setup

```bash
# Install dependencies using uv
uv sync

# Activate virtualenv
. .venv/bin/activate

# Copy environment file and configure
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load demo data
python manage.py loaddata demo_data.json
```

### Running the Development Server

```bash
# Standard development server
python manage.py runserver

# With ASGI support (for WebSockets)
python manage.py runserver --noreload
```

### Database Operations

```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create a database dump
python manage.py dumpdata > backup.json
```

### Testing

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test characters

# Run specific test
python manage.py test characters.tests.TestCharacterModel
```

### Static Files

```bash
# Collect static files
python manage.py collectstatic

# SCSS compilation happens automatically via django-libsass during collection
```

### Management Commands

```bash
# Delete anonymous characters (custom command)
python manage.py delete_anonymous_characters

# Check for duplicate entries (custom command)
python manage.py dupes
```

## Architecture

### Multi-Tenancy via Worlds

The platform supports multiple independent RPG worlds/systems:
- Each `World` model instance represents a separate game system or setting
- Worlds are selected via domain name through `WorldFromDomainNameMiddleware`
- Each request has `request.world` set by the middleware based on the `Host` header
- Worlds can have custom branding (logo, name, colors), SCSS themes, and extensions
- Characters, items, spells, etc. are filtered by world via the `Extension` system

### Homebrew Content System

Many models inherit from `HomebrewModel`, which provides:
- `is_homebrew`: Flag for user-created content
- `homebrew_campaign`: Links content to specific campaigns
- `homebrew_character`: Links content to specific characters
- `HomebrewQuerySet` with filtering methods: `.homebrew()`, `.without_homebrew()`

This allows users to create custom content scoped to their campaigns or characters without affecting the base game.

### Extension System

Core to content organization:
- `Extension` model (in `rules` app) defines game modules/systems
- Extensions can be world-specific (type='w') or general
- Characters must have extensions to access related content (items, spells, etc.)
- QuerySets filter by extension: `Character.objects.for_world(world)`

### Character Modifiers

Characters have complex stat calculation via modifier system:
- `TemplateModifier`: Modifiers from character templates (classes, occupations)
- `RiotGearModifier`: Modifiers from equipped armor
- `QuirkModifier`: Modifiers from horror quirks
- `BodyModificationModifier`: Modifiers from body augmentations
- `SpellTemplateModifier`: Modifiers from learned spells

The `ModifierBaseQuerySet` aggregates modifiers across all sources with methods like:
- `.for_character(character)`: Get all modifiers for a character
- `.skill_modifier_sum(skill)`: Sum modifiers for a skill
- `.aspect_modifier_sum(aspect)`: Sum modifiers for character aspects

### Multi-language Support

Uses `django-transmeta` for model field translations:
- Models use `metaclass=TransMeta` with `translate` tuple in Meta
- Fields automatically get `_de`, `_en` variants
- Active language determines which variant is used
- Default language is German (`LANGUAGE_CODE = "de"`)

### PDF Generation

Uses `django-bootyprint` (wraps WeasyPrint) for PDF exports:
- Character sheets can be exported to PDF
- Rulebooks are generated as PDFs
- Configuration in settings: `BOOTYPRINT` dict
- PDFs use print-specific CSS via `@media print`

### WebSocket Support

Django Channels for real-time features:
- Campaign dice rolling uses WebSockets (`campaigns/consumers.py`)
- Redis backend for channel layer
- ASGI application configured in `phasesix/asgi.py`
- Routing defined in `campaigns/routing.py`

### Modals and Sidebars

Custom JavaScript framework (`modals_sidebars` app):
- Data attribute-driven modals and sidebars
- Fetch forms: `data-fetch-form="true"` for AJAX form submission
- Modal triggers: `data-modal-url` for modal content
- Sidebar triggers: `data-sidebar-right-url` for offcanvas sidebars
- Action triggers: `data-action-trigger-url` for POST requests
- See `/modals_sidebars/modals_sidebars.md` for full documentation

### RSS Feeds

The platform provides RSS feeds for new and modified content:
- `feeds/new_admin/`: Latest new items across the platform
- `feeds/modified_admin/`: Latest modified items
- Feeds include characters, items, spells, recipes, foes, body modifications

## App Structure

- `characters`: Core character models, creation, sheets
- `campaigns`: Campaign management, dice rolling, WebSocket consumers
- `rules`: Core game rules (skills, templates, lineages, extensions, foes)
- `armory`: Items, weapons, riot gear (armor), currency
- `magic`: Spells and spell systems
- `pantheon`: Deities and priest actions
- `horror`: Horror quirks and sanity mechanics
- `body_modifications`: Cybernetic/biological augmentations
- `vehicles`: Vehicle management
- `potions`: Potion/brewing system
- `homebrew`: Base models for user-created content
- `worlds`: Multi-tenant world system, wiki pages
- `rulebook`: Digital rulebook chapters and PDFs
- `forum`: Discussion forums
- `portal`: Landing pages, user profiles, registration
- `curators_desk`: Administrative utilities
- `api`: REST API endpoints with API key authentication
- `plots`: Plot/story management
- `eventstream`: Server-sent events for real-time updates
- `modals_sidebars`: Frontend modal/sidebar framework

## Coding Guidelines

Project follows guidelines in `/guidelines.md`:

### Django Patterns
- Use Bootstrap 5 and `django_bootstrap5` template tags (avoid custom CSS)
- Use `{% bootstrap_form %}` and `{% bootstrap_field %}` tags for forms
- Follow Django's "batteries included" philosophy
- Use `get_object_or_404` for object retrieval
- Use `select_related` and `prefetch_related` to optimize queries

### Models
- Always add `__str__` methods
- Use `related_name` for foreign keys
- Define `Meta` class with `ordering` and `verbose_name`
- `blank=True` for optional form fields, `null=True` for optional DB fields

### Templates
- Use template inheritance
- Load static files with `{% load static %}`
- Always include `{% csrf_token %}` in forms
- Avoid complex logic—use template tags or move to views

### Code Style
- PEP 8 with 120 character line limit
- Double quotes for strings
- f-strings for formatting
- Sort imports with `isort`

## Environment Configuration

Required `.env` variables:
- `DEBUG`: Enable/disable debug mode
- `SECRET_KEY`: Django secret key
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `BASE_URL`: Base URL for the application
- `DATABASE_*`: Database configuration (leave `DATABASE_ENGINE` unset for SQLite)
- `REDIS_HOST`, `REDIS_PORT`: Redis configuration for caching and channels
- `EMAIL_*`: Email server configuration
- `STATIC_URL`, `STATIC_ROOT_RELATIVE`: Static files configuration
- `MEDIA_URL`, `MEDIA_ROOT_RELATIVE`: Media files configuration

## Docker

```bash
# Start services
docker-compose up

# Run migrations
docker-compose exec web venv/bin/python manage.py migrate

# Load demo data
docker-compose exec web venv/bin/python manage.py loaddata demo_data.json

# Create superuser
docker-compose exec web venv/bin/python manage.py createsuperuser
```

## Admin Interface

Uses `django-unfold` for modern admin UI:
- Custom navigation defined in settings: `UNFOLD['SIDEBAR']['navigation']`
- Organized into sections: Characters/Campaigns, Armory, Extensions, Rules, Worlds
- Access at `/admin/` after creating superuser
