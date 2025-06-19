# WeasyStrap

A lightweight Bootstrap alternative designed specifically for WeasyPrint. This library provides a simplified version of Bootstrap's core functionality that works well with WeasyPrint for PDF generation.

## Features

- Typography styling
- Grid system
- Layout components
- Spacing utilities
- Color utilities
- Flexbox utilities

## Usage

To use WeasyStrap in your Django templates for WeasyPrint PDF generation:

```html
{% load static %}
<link rel="stylesheet" href="{% static 'rulebook/weasystrap/weasystrap.css' %}">
```

## Components

### Grid System

WeasyStrap includes a simplified 12-column grid system:

```html
<div class="container">
  <div class="row">
    <div class="col-6">Half width</div>
    <div class="col-6">Half width</div>
  </div>
</div>
```

### Typography

Basic typography classes are available:

```html
<h1 class="display-4">Large heading</h1>
<p class="lead">Lead paragraph</p>
<p class="text-muted">Muted text</p>
```

### Spacing

Margin and padding utilities:

```html
<div class="mt-3 mb-4 p-2">Spaced content</div>
```

### Colors

Background and text color utilities:

```html
<div class="bg-primary text-white">Colored box</div>
```

## Notes

This is a minimal implementation focused on PDF generation with WeasyPrint. It does not include JavaScript components or interactive elements.
