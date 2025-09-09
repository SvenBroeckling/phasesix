# Modals and Sidebars

Modals and Sidebars are used to display information in a modal or sidebar. They are implemented as a set of data attribute configurations and Javascript events.

They have interoperability with HTMX, Bootstrap Modals and Bootstrap Offcanvas. All fetched content is processed by HTMX, so HTMX events work well.

## Forms

Forms can be marked as `fetch()` forms by specifying the data attribute `data-fetch-form="true"`. At that moment, a
central event handler (in `modals_sidebars/js/fetch_form.js`) intercepts the submit event, sends the form via `fetch()`,
and acts according to the response of a Django `UpdateView`, `FormView` or similar.

To implement a fetch form, the following steps are required:

* The surrounding container into which the form is loaded must have the CSS class `.fetch-form-container`. **Modal** and
  **Sidebar** have this container automatically.
* The `form` itself must have a valid `action` set to a Django `UpdateView` or comparable.
* The `form` must contain a `{% csrf_token %}` as usual.
* Optionally, `data-fetch-form-close="sidebar|modal|all"` can be used to control whether the Modal and/or Sidebar should
  be closed in case of success.
* If the `form` contains a spinner with the class `form-submit-spinner` anywhere within it, it will be automatically
  displayed while `fetch()` is running.

When these prerequisites are met, the top-level *Submit* handler automatically intercepts the submit and sends the data
via `fetch()`.

The response of the `POST` call is loaded into the `.fetch-form-container` element closest to the `form`, following
Django's redirect. This applies both to the error case, where Django renders the form with error messages, and to the
success case, where the call specified by `success_url` is inserted.

### Example

```html

<form
    data-fetch-form="true"
    data-fetch-form-close="all"
    data-fetch-form-event-after="modal-hide"
    data-fetch-form-event-on-render="toast-show,header-blink"
    action="{% url 'myapp:object_update' pk=object.id %}"
    method="post">
    {% csrf_token %}
    {{ form.media }}

    {% bootstrap_form form layout="floating" %}
    <button type="submit" class="btn btn-primary">
        <span class="form-submit-spinner spinner-border spinner-border-sm d-none" role="status"
              aria-hidden="true"></span>
        {% trans "Save" %}
    </button>
</form>
```

## Modals

A central modal is added to the base template, which can be triggered via `data-` attributes. To open the modal on a link or button, it is sufficient to specify `data-modal-url="url"`. Additionally, some options are available.

To add the modal to the base template, the template tag `{% site_modal %}` can be used.

```html
{% load modals_sidebars %}
{% site_modal%}
```

### Data Attribute

* `data-modal-url`: **Required** This URL is fetched via `fetch()` with the method GET.
* `data-modal-title`: Gives a title to the modal.
* `data-modal-body`: If set, the given content is copied as the first content in the modal.
* `data-modal-body-from-id`: If set to an HTML ID (`#mytemplate`), the content of this element is copied into the modal.
* `data-modal-refresh-after`: If set to "true", the current page is reloaded after closing the modal.
* `data-modal-event-after`: A comma separated list of event names to be dispatched from `document` after the modal is closed.
* `data-modal-event-show`:  A comma separated list of event names to be dispatched from `document` after the modal is shown.
* `data-modal-iframe="true"`: If set, the content of the modal is loaded into an `iframe` and **not** via `fetch()`.
* `data-modal-size-class`: Set the Bootstrap CSS class to the modal. Options are `modal-sm`, `modal-lg`, `modal-xl` and `modal-fullscreen`
* `data-modal-confirm-close`: If set to "true", the modal is closed only after a confirmation prompt is accepted via `confirm()`.
* `modal-auto-show-query-string`: If this query string parameter is present, the modal is automatically opened when the query string parameter is present in the URL.

### Events

The following events can be dispatched via Javascript to influence the modal:

* `modal-hide`: The modal is hidden and cleared.
* `modal-show`: The modal is shown with the current content.
* `modal-fetch-and-show`: A URL is fetched via GET and shown in the modal. The event must be a `CustomEvent` with the same `detail` object as the data set in the HTML (data-modal-url is mapped to modalUrl).

### Examples

Trigger a modal via HTML

```html

<button
    class="btn btn-outline-primary"
    type="button"
    data-modal-url="{% url 'my_app:object_update' pk=object.id %}"
    data-modal-title="{% trans 'PDF Preview - Object' %}"
    data-modal-body-from-id="#modal-pdf-loading-body">

    <template id="modal-pdf-loading-body">
        <div class="flex-centered h-100 w-100">
            <i class="fa fa-file-pdf"></i>
        </div>
    </template>
```

Trigger a modal via JavaScript

```javascript
    document.dispatchEvent(
    new CustomEvent('modal-fetch-and-show', {
        detail: {
            modalTitle: fetchAfterTitle,
            modalUrl: fetchAfter
        }
    })
)
```

## Sidebar

The sidebar behaves similar to the modal and offers the same mechanisms. The sidebar uses a Bootstrap `Offcanvas`
element, but there is currently only a `SidebarRight` known. A sidebar on the left side does not yet exist.

### Data Attribute

* `data-sidebar-right-url`:  **Required** This URL is fetched via `fetch()` with the method GET.
* `data-sidebar-right-title`: Gives a title to the sidebar.
* `data-sidebar-right-body`: If set, the given content is copied as the first content in the sidebar.
* `data-sidebar-right-body-from-id`: If set to an HTML ID (`#mytemplate`), the content of this element is copied into the sidebar.
* `data-sidebar-right-iframe="true"`: If set, the content of the sidebar is loaded into an `iframe` and **not** via `fetch()`.
* `data-sidebar-right-event-show`:  A comma separated list of event names to be dispatched from `document` after the sidebar is shown.
* `data-sidebar-right-event-after`: A comma separated list of event names to be dispatched from `document` after the sidebar is closed.

### Events

The following events can be dispatched in Javascript to influence the sidebar:

* `sidebar-right-hide`: The sidebar is hidden and cleared.
* `sidebar-right-show`: The sidebar is shown with the current content.
* `sidebar-right-fetch-and-show`:  A URL is fetched via GET and shown in the sidebar. The event must be a `CustomEvent` with the same `detail` object as the data set in the HTML (data-sidebar-right-url is mapped to sidebarRightUrl).

### Examples


Trigger a sidebar via HTML

```html

<button
    data-sidebar-title="Edit"
    data-sidebar-url="{% url 'my_app:object_update' pk=object.id %}"
    class="btn btn-outline-primary btn-sm d-inline-flex align-items-center">
    <i class="fa fa-pencil"></i>
    <span class="ms-2">Edit</span>
</button>
```

Trigger a sidebar via JavaScript

```javascript
    document.dispatchEvent(
    new CustomEvent('sidebar-right-fetch-and-show', {
        detail: {
            sidebarTitle: fetchAfterTitle,
            sidebarUrl: fetchAfter
        }
    })
```

## Action Triggers

Often you want to trigger an asyncronous request via POST with information contained in the URL. **Action Triggers** allow
this by using custom `data-` attributes in the HTML. To convert an element into a post trigger, the data attribute
`data-action-trigger="true"` must be set.

The default event of the element is disabled in this case.

### Data Attributes

* `data-action-trigger-url`: **Required** This URL is fetched via `fetch()` with the method POST.
* `data-action-trigger-method`: The HTTP method to use, defaults to `POST`.
* `data-action-trigger-event-type`: When to trigger, defaults to `click`. Can be set to `change`.
* `data-action-trigger-event-after`: If set to a name, a CustomEvent with the given name from `document` is dispatched, once the post request is sent. If set to a comma separated list of event names, each event is dispatched after the modal is closed.

### Events

Action Triggers have no event listeners.

### Example


An example for a post trigger from the cart. The `POST` view deletes a position from a cart.

```html
    <a data-action-trigger-url="{% url 'shop:cart_delete_position' cart_position_pk=position.id %}"
       data-action-trigger-event-typ="change"
       data-action-trigger-method="DELETE"
       data-action-trigger-event-after="refresh-cart"
       class="btn btn-outline-danger btn-sm d-inline-flex align-items-center">
         <i class="fa fa-trash"></i>
         <span class="ms-2">Delete</span>
    </a>
```

