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
* `data-modal-event-after`: If set to a name, a CustomEvent with the given name from `document` is dispatched, once the modal is closed.
* `data-modal-event-show`: If set to a name, a CustomEvent with the given name from `document` is dispatched, once the modal is shown.
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

Die Sidebar verhält sich analog zum Modal und bietet die selben Mechaniken. Die Sidebar verwendet ein Bootstrap
`Offcanvas` Element, es ist aber zu unserem Code hin bislang eine `SidebarRight` bekannt. Eine Sidebar auf der linken
Seite gibt es noch nicht.

### Data Attribute

* `data-sidebar-right` aktiviert die Sidebar, wenn es auf true gesetzt ist.
* `data-sidebar-title` gibt einen Titel an, der in der Sidebar verwendet wird.
* Wenn `data-sidebar-body` gesetzt ist, wird der angegebene Inhalt als erstes in die Sidebar kopiert.
* Wenn `data-sidebar-body-from-id` mit einem HTML ID gefüllt ist (`#meintemplate`), wird der Inhalt dieses Elements in
  die Sidebar kopiert.
* Ist eine `data-sidebar-url` angegeben, wird als letztes diese URL via `fetch()` mit der methode GET abgerufen.
* Ist `data-sidebar-iframe="true"` angegeben, so wird der Inhalt der Sidebar in ein `iframe` geladen, und **nicht** via
  `fetch()` abgerufen.
* `data-sidebar-event-after` wenn auf einen Namen gesetzt wird ein CustomEvent mit dem angegebenen Namen von `document`
  dispatched.

### Events

*Neu nach Merge Request !33*

Folgende Events können im Javascript dispatched werden, um die Sidebar zu beeinflussen:

* `sidebar-right-hide`: Die Sidebar wird ausgeblendet und geleert.
* `sidebar-right-show`: Die Sidebar wird mit aktuellem Inhalt angezeigt
* `sidebar-right-fetch-and-show`: Es wird eine URL per GET abgerufen und danach in der Sidebar angezeigt. Das Event muss
  ein `CustomEvent` sein, das `detail` Object enthält die selben Elemente wie das DataSet im HTML (
  data-sidebar-right-url wird zu sidebarRightUrl)

### Beispiele

Sidebar im HTML triggern

```html

<button
    data-sidebar-right="true"
    data-sidebar-title="{% trans " Bearbeiten" %}"
data-sidebar-url="{% url 'property_management:residential_object_update' pk=object.id %}"
class="btn btn-outline-primary btn-sm d-inline-flex align-items-center">
{% svg_symbol 'pencil' 14 14 %}
<span class="ms-2">{% trans 'Bearbeiten' %}</span>
</button>
```

Sidebar im JavaScript triggern

```javascript
    document.dispatchEvent(
    new CustomEvent('sidebar-right-fetch-and-show', {
        detail: {
            sidebarTitle: fetchAfterTitle,
            sidebarUrl: fetchAfter
        }
    })
```

## Post Trigger

Oft möchte man durch einen Klick auf einen Button oder einen Link einfach einen asyncronen Request via POST auslösen,
dessen Informationen bereits in der URL durch Keyword Arguments vorhanden sind. **Post Trigger** ermöglichen dies durch
eigene `data-` Angaben im HTML. Um ein Element in einen Post Trigger zu verwandeln, muss das Data Attribut
`data-post-trigger="true"` gesetzt werden.

Das Default Event des Elements wird hierdurch deaktiviert.

### Data Attribute

* `data-post-trigger` aktiviert den Post Trigger auf dem Element.
* `data-post-trigger-url` gibt die URL an, die via `POST` aufgerufen wird.
* `data-post-trigger-refresh-after` wenn auf "true" gesetzt wird die aktuelle Seite nach dem POST neu geladen.
* `data-post-trigger-fetch-after`: wenn dieses Attribut gesetzt ist und eine URL enthält wird nach erfolgreichem `POST`
  ein `GET` auf diese URL ausgeführt. Dies kann genutzt werden, um ein Resultat anzuzeigen.
* `data-post-trigger-fetch-after-target` gibt das Ziel des nachträglichen `GET` Aufrufs an. Dies kann eine der folgenden
  Optionen sein:
    * `modal`: Das Ergebnis wird im Modal angezeigt, das Modal wird geöffnet
    * `sidebar`: Das Ergebnis wird in der Sidebar angezeigt, die Sidebar wird geöffnet
    * Ein Selector: Wenn das Attribut gefüllt ist und nicht `modal` oder `sidebar` enthält, wird der CSS Selector im DOM
      angefragt und das Ergebnis in den bestehenden DOM eingefügt.
* `data-post-trigger-fetch-after-title`: Für die Optionen `modal` und `sidebar` kann hier der zu verwendende Titel
  angegeben werden.

### Events

Post Trigger haben keine Event Listener.

### Beispiel

Ein Beispiel für den Post Trigger aus dem Warenkorb. Die `POST` View löscht eine Position aus dem Warenkorb, die "fetch
after" View ist der Sidebar Warenkorb selbst, so wird die Anzeige aktualisiert.

```html
    <a
    data-post-trigger="true"
    data-post-trigger-url="{% url 'shop:cart_delete_position' cart_position_pk=position.id %}"
    data-post-trigger-fetch-after="{% url " shop:cart_sidebar" %}"
data-post-trigger-fetch-after-target="sidebar"
class="float-end cursor-pointer">
{% svg_symbol 'x-lg' 24 24 color="gray" %}
</a>
```

