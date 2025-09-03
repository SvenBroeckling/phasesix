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

A central modal is added to the base template, which can be triggered via `data-` attributes. To open the modal on a
link
or button, it is sufficient to specify `data-modal-url="url"`. Additionally, some options are available.

To add the modal to the base template, the template tag `{% site_modal %}` can be used.

```html
{% load modals_sidebars %}
{% site_modal%}
```

### Data Attribute

* `data-modal-title` gibt einen Titel an, der im Modal verwendet wird.
* Wenn `data-modal-body` gesetzt ist, wird der angegebene Inhalt als erstes in das Modal kopiert.
* Wenn `data-modal-body-from-id` mit einem HTML ID gefüllt ist (`#meintemplate`), wird der Inhalt dieses Elements in das
  Modal kopiert.
* Ist eine `data-modal-url` angegeben, wird als letztes diese URL via `fetch()` mit der methode GET abgerufen.
* `data-modal-refresh-after` wenn auf "true" gesetzt wird die aktuelle Seite nach dem Schließen des Modals neu geladen.
* `data-modal-event-after` wenn auf einen Namen gesetzt wird ein CustomEvent mit dem angegebenen Namen von `document`
  dispatched, sobald das Modal geschlossen wird.
* `data-modal-event-show` wenn auf einen Namen gesetzt wird ein CustomEvent mit dem angegebenen Namen von `document`
  dispatched, sobald das Modal angezeigt wird.
* Ist `data-modal-iframe="true"` angegeben, so wird der Inhalt des Modals in ein `iframe` geladen, und **nicht** via
  `fetch()` abgerufen.
* Ist `data-modal-size-class` angegeben, wird die CSS Klasse in das Modal übernommen. Hier kann `modal-fullscreen`
  verwendet werden, um ein Vollbild Modal zu erreichen.
* Ist `data-modal-confirm-close` angegeben, wird das Modal erst nach einer Bestätigung via `confirm()` geschlossen,
  wobei der Inhalt des Data Attributs den Prompt enthält.
* `modal-auto-show-query-string`: Ist hier ein QueryString Parameter angegeben, wird das Modal automatisch geöffnet,
  wenn der QueryString Parameter in der URL vorhanden ist.

Diese Mechanik kann genutzt werden, um mit -body eine Anzeige zu schaffen, die während des `fetch()` Ladevorgangs zu
sehen ist.

### Events

Folgende Events können im Javascript dispatched werden, um das Modal zu beeinflussen:

* `modal-hide`: Das Modal wird ausgeblendet und geleert.
* `modal-show`: Das Modal wird mit aktuellem Inhalt angezeigt
* `modal-fetch-and-show`: Es wird eine URL per GET abgerufen und danach im Modal angezeigt. Das Event muss ein
  `CustomEvent` sein, das `detail` Object enthält die selben Elemente wie das DataSet im HTML (data-modal-url wird zu
  modalUrl)

### Beispiele

Modal im HTML triggern

```html

<button
    class="btn btn-outline-primary"
    type="button"
    data-modal-url="{% url 'property_management:residential_object_update' pk=object.id %}"
    data-modal-title="{% trans 'PDF Vorschau - Objekt' %}"
    data-modal-body-from-id="#modal-pdf-loading-body">

    <template id="modal-pdf-loading-body">
        <div class="flex-centered h-100 w-100">
            {% svg_symbol 'filetype-pdf' 128 128 color="#999" %}
        </div>
    </template>
```

Modal im JavaScript triggern

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

