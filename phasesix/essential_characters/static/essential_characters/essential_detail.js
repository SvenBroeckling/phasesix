document.querySelectorAll("[data-essential-image-input]").forEach((input) => {
  input.form
    .querySelector("[data-essential-image-picker]")
    .addEventListener("click", () => input.click());

  input.addEventListener("change", () => {
    if (input.files.length) {
      input.form.requestSubmit();
    }
  });
});

document.querySelectorAll("[data-essential-image-remove]").forEach((button) => {
  button.addEventListener("click", (event) => {
    if (!window.confirm(button.dataset.confirmMessage)) {
      event.preventDefault();
    }
  });
});

document.querySelectorAll("[data-essential-condition-url]").forEach((button) => {
  button.addEventListener("click", () => {
    const row = button.closest(".essential-readonly-ranks");
    const body = new URLSearchParams({ value: button.dataset.essentialConditionValue });

    fetch(button.dataset.essentialConditionUrl, {
      method: "POST",
      body,
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": document.body.dataset.csrfToken,
      },
    }).then((response) => {
      if (!response.ok) {
        return;
      }
      row.querySelectorAll(".essential-rank-circle").forEach((circle) => {
        circle.classList.toggle("selected", circle === button);
      });
    });
  });
});

function initializeAjaxPicker(picker) {
  if (picker.dataset.initialized) return;
  picker.dataset.initialized = "true";
  const select = picker.querySelector("select");
  const search = picker.querySelector("[data-essential-ajax-search]");
  const results = picker.querySelector("[data-essential-ajax-results]");
  const selected = picker.querySelector("[data-essential-ajax-selected]");
  let requestNumber = 0;
  let timer;

  function renderSelected() {
    selected.replaceChildren();
    Array.from(select.selectedOptions).forEach((option) => {
      const row = document.createElement("div");
      row.className = "essential-ajax-picker-selection";

      const label = document.createElement("span");
      label.textContent = option.text;

      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "essential-ajax-picker-remove";
      remove.setAttribute("aria-label", `${picker.dataset.removeLabel}: ${option.text}`);
      remove.innerHTML = '<i class="fas fa-times" aria-hidden="true"></i>';
      remove.addEventListener("click", () => {
        option.remove();
        renderSelected();
      });
      row.append(label, remove);
      selected.append(row);
    });
  }

  function addResult(result) {
    let option = Array.from(select.options).find(
      (candidate) => candidate.value === String(result.id),
    );
    if (!option) {
      option = new Option(result.text, result.id, true, true);
      select.add(option);
    }
    option.selected = true;
    search.value = "";
    results.hidden = true;
    renderSelected();
  }

  function renderResults(items) {
    const selectedValues = new Set(
      Array.from(select.selectedOptions).map((option) => option.value),
    );
    results.replaceChildren();
    items
      .filter((item) => !selectedValues.has(String(item.id)))
      .forEach((item) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "list-group-item list-group-item-action";
        const label = document.createElement("strong");
        label.textContent = item.text;
        button.append(label);
        if (item.meta) {
          const meta = document.createElement("small");
          meta.textContent = item.meta;
          button.append(meta);
        }
        button.addEventListener("click", () => addResult(item));
        results.append(button);
      });
    results.hidden = results.children.length === 0;
  }

  function searchResources() {
    const currentRequest = ++requestNumber;
    const url = new URL(picker.dataset.searchUrl, window.location.origin);
    url.searchParams.set("type", picker.dataset.searchType);
    url.searchParams.set("q", search.value.trim());
    if (picker.dataset.searchType === "spells") {
      const aspectSelect = picker
        .closest(".essential-edit-form")
        ?.querySelector('[data-search-type="magic_aspects"] select');
      Array.from(aspectSelect?.selectedOptions || []).forEach((option) => {
        url.searchParams.append("origin", option.value);
      });
    }
    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (currentRequest === requestNumber) renderResults(data.results || []);
      });
  }

  search.addEventListener("input", () => {
    window.clearTimeout(timer);
    timer = window.setTimeout(searchResources, 180);
  });
  search.addEventListener("focus", searchResources);
  search.addEventListener("keydown", (event) => {
    if (event.key === "Escape") results.hidden = true;
  });
  document.addEventListener("click", (event) => {
    if (!picker.contains(event.target)) results.hidden = true;
  });
  renderSelected();
}

function initializeEditForm(root = document) {
  root.querySelectorAll?.("[data-essential-ajax-picker]").forEach(initializeAjaxPicker);
}

document.addEventListener("change", (event) => {
  if (!event.target.matches(".essential-edit-form input.essential-rank-input")) return;
  const group = event.target.closest(".essential-rank-input");
  group.querySelectorAll(".essential-rank-circle").forEach((circle) => {
    circle.classList.toggle("selected", Boolean(circle.querySelector("input:checked")));
  });
});

initializeEditForm();
new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    mutation.addedNodes.forEach((node) => {
      if (node.nodeType === Node.ELEMENT_NODE) initializeEditForm(node);
    });
  });
}).observe(document.body, { childList: true, subtree: true });
