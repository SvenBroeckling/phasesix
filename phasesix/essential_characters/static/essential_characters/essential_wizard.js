document.addEventListener("DOMContentLoaded", () => {
  const wizard = document.querySelector(".essential-wizard");
  if (!wizard) return;

  const localizedRandomText = {
    de: {
      names: ["Arel von Bayard", "Mara Schattenhain", "Joran Aschpfad", "Selka Rotmund"],
      concepts: [
        "Ein ehemaliger Soldat, der einen alten Eid nicht loswird.",
        "Eine Kräuterkundige mit Wissen über verbotene Rituale.",
        "Ein abtrünniger Inquisitor auf der Suche nach Vergebung.",
        "Eine fahrende Händlerin mit Schulden bei den falschen Leuten.",
      ],
      months: [
        "Schneemond", "Festmond", "Frühlingsmond", "Hagelmond", "Lebensmond", "Sommermond",
        "Obstmond", "Haumond", "Herbstmond", "Weinmond", "Nebelmond", "Wintermond",
      ],
      oaths: [
        "Ich schulde einem alten Lehrmeister ein Leben.",
        "Ich habe geschworen, eine verlorene Familie wiederzufinden.",
        "Ich darf den Namen eines Toten nicht vergessen.",
        "Ich habe eine Schuld gegenüber meiner letzten Gemeinschaft.",
      ],
      foci: ["Geschwärzter Ring", "Knochenamulett", "Alte Münze"],
      rituals: [
        "Stille Wache vor Morgengrauen",
        "Asche und Salz erneuern",
        "Namen der Toten murmeln",
      ],
    },
    en: {
      names: ["Arel von Bayard", "Mara Shadowgrove", "Joran Ashpath", "Selka Redmouth"],
      concepts: [
        "A former soldier haunted by an old oath.",
        "A herbalist with knowledge of forbidden rituals.",
        "A renegade inquisitor searching for forgiveness.",
        "A traveling merchant indebted to the wrong people.",
      ],
      months: [
        "Snowmoon", "Feastmoon", "Springmoon", "Hailmoon", "Lifemoon", "Summermoon",
        "Orchardmoon", "Wheatmoon", "Fallmoon", "Winemoon", "Fogmoon", "Wintermoon",
      ],
      oaths: [
        "I owe an old mentor my life.",
        "I swore to find a lost family.",
        "I must not forget the name of a dead person.",
        "I owe a debt to my last community.",
      ],
      foci: ["Blackened ring", "Bone amulet", "Old coin"],
      rituals: [
        "Keep silent watch before dawn",
        "Renew ash and salt",
        "Murmur the names of the dead",
      ],
    },
  };
  const language = document.documentElement.lang?.split("-")[0] || "en";
  const randomText = localizedRandomText[language] || localizedRandomText.en;

  function field(name) {
    return wizard.querySelector(`[name$="-${name}"]`);
  }

  const groups = () => {
    const inputs = Array.from(wizard.querySelectorAll("input.essential-rank-input"));
    return [...new Set(inputs.map((input) => input.name))].map(
      (name) => inputs.filter((input) => input.name === name),
    );
  };

  function renderCircles() {
    wizard.querySelectorAll(".essential-rank-circle").forEach((circle) => {
      circle.classList.toggle("selected", Boolean(circle.querySelector("input:checked")));
    });
  }

  function shuffle(values) {
    for (let index = values.length - 1; index > 0; index -= 1) {
      const other = Math.floor(Math.random() * (index + 1));
      [values[index], values[other]] = [values[other], values[index]];
    }
    return values;
  }

  function randomItem(values) {
    return values[Math.floor(Math.random() * values.length)];
  }

  function setValue(input, value) {
    if (!input) return;
    input.value = value;
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function selectableOptions(select, predicate = () => true) {
    if (!select) return [];
    return Array.from(select.options).filter(
      (option) => option.value && !option.disabled && predicate(option),
    );
  }

  function randomizeSelect(select, excludedValues = []) {
    const options = selectableOptions(select, (option) => !excludedValues.includes(option.value));
    if (options.length) setValue(select, randomItem(options).value);
  }

  function randomizeMultipleSelect(select, count, predicate = () => true) {
    const selected = shuffle(selectableOptions(select, predicate)).slice(0, count);
    Array.from(select?.options || []).forEach((option) => {
      option.selected = selected.includes(option);
    });
    select?.dispatchEvent(new Event("change", { bubbles: true }));
    return selected.map((option) => option.value);
  }

  function randomizeRanks(values) {
    const randomizedValues = shuffle(values);
    groups().forEach((group, index) => {
      const input = group.find((candidate) => Number(candidate.value) === randomizedValues[index]);
      if (input) input.checked = true;
    });
    renderCircles();
  }

  function randomizeConcept() {
    const century = Math.floor(Math.random() * 10) + 1;
    const year = (century - 1) * 100 + Math.floor(Math.random() * 100) + 1;
    const month = Math.floor(Math.random() * 12);
    const day = Math.floor(Math.random() * 28) + 1;
    setValue(field("name"), randomItem(randomText.names));
    setValue(field("concept"), randomItem(randomText.concepts));
    setValue(field("oath_or_debt"), randomItem(randomText.oaths));
    setValue(field("century"), century);
    setValue(field("birth_date"), `${day}. ${randomText.months[month]} ${year}`);
  }

  function randomizeMarks() {
    ["ancestry", "path", "bond"].forEach((name) => randomizeSelect(field(name)));
  }

  function randomizeEquipment() {
    randomizeSelect(field("primary_weapon"));
    randomizeSelect(field("secondary_weapon"), [field("primary_weapon")?.value]);
    randomizeSelect(field("armor"));
    const itemCount = Math.min(selectableOptions(field("items")).length, 3);
    randomizeMultipleSelect(field("items"), itemCount);
  }

  function randomizeSupernatural() {
    const aspects = Array.from(wizard.querySelectorAll('[name*="-magic_aspect_"]'));
    const spells = Array.from(wizard.querySelectorAll('[name*="-spell_"]'));
    spells.forEach((select) => setValue(select, ""));
    aspects.forEach((select, index) => {
      randomizeSelect(select, aspects.slice(0, index).map((aspect) => aspect.value));
    });
    updateSpellOptions();
    spells.forEach((select) => randomizeSelect(select));
    setValue(field("focus"), randomItem(randomText.foci));
    setValue(field("regeneration_ritual"), randomItem(randomText.rituals));
  }

  function initializeItemPicker(picker) {
    const select = picker.querySelector("select");
    const search = picker.querySelector("[data-essential-item-search]");
    const addButton = picker.querySelector("[data-essential-item-add]");
    const optionsContainer = picker.querySelector("[data-essential-item-options]");
    const selectedContainer = picker.querySelector("[data-essential-item-selected]");
    let pendingOption = null;

    function availableOptions() {
      const query = search.value.trim().toLocaleLowerCase();
      return Array.from(select.options)
        .filter((option) => !option.selected)
        .filter((option) => !query || option.text.toLocaleLowerCase().includes(query))
        .slice(0, 8);
    }

    function renderOptions() {
      const options = availableOptions();
      optionsContainer.replaceChildren();
      optionsContainer.hidden = options.length === 0;
      options.forEach((option) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "list-group-item list-group-item-action";
        button.textContent = option.text;
        button.addEventListener("click", () => {
          pendingOption = option;
          search.value = option.text;
          addButton.disabled = false;
          optionsContainer.hidden = true;
          search.focus();
        });
        optionsContainer.append(button);
      });
    }

    function renderSelected() {
      selectedContainer.replaceChildren();
      Array.from(select.selectedOptions).forEach((option) => {
        const row = document.createElement("div");
        row.className = "essential-item-picker-selection";

        const label = document.createElement("span");
        label.textContent = option.text;

        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.className = "btn btn-sm btn-outline-danger";
        removeButton.setAttribute("aria-label", `${picker.dataset.removeLabel}: ${option.text}`);
        removeButton.innerHTML = '<i class="fas fa-times" aria-hidden="true"></i>';
        removeButton.addEventListener("click", () => {
          option.selected = false;
          select.dispatchEvent(new Event("change", { bubbles: true }));
        });

        row.append(label, removeButton);
        selectedContainer.append(row);
      });
    }

    function resetSearch() {
      pendingOption = null;
      search.value = "";
      addButton.disabled = true;
      optionsContainer.hidden = true;
    }

    search.addEventListener("input", () => {
      pendingOption = null;
      addButton.disabled = true;
      renderOptions();
    });
    search.addEventListener("focus", renderOptions);
    search.addEventListener("keydown", (event) => {
      if (event.key === "Escape") resetSearch();
      if (event.key === "Enter" && pendingOption) {
        event.preventDefault();
        addButton.click();
      }
    });
    addButton.addEventListener("click", () => {
      if (!pendingOption) return;
      pendingOption.selected = true;
      select.dispatchEvent(new Event("change", { bubbles: true }));
      resetSearch();
    });
    select.addEventListener("change", () => {
      renderSelected();
      renderOptions();
    });
    document.addEventListener("click", (event) => {
      if (!picker.contains(event.target)) optionsContainer.hidden = true;
    });
    renderSelected();
  }

  function selectedOriginValues() {
    return Array.from(wizard.querySelectorAll('[name*="-magic_aspect_"]'))
      .map((select) => select.value)
      .filter(Boolean);
  }

  function updateSpellOptions() {
    const origins = selectedOriginValues();
    const selects = Array.from(wizard.querySelectorAll("[data-essential-spell-picker] select"));
    selects.forEach((select) => {
      const otherValues = selects
        .filter((other) => other !== select)
        .map((other) => other.value)
        .filter(Boolean);
      Array.from(select.options).forEach((option) => {
        if (!option.value) return;
        option.disabled =
          !origins.includes(option.dataset.origin) || otherValues.includes(option.value);
      });
      if (select.selectedOptions[0]?.disabled) setValue(select, "");
      select.dispatchEvent(new CustomEvent("essential:spell-options-updated"));
    });
  }

  function initializeSpellPicker(picker) {
    const select = picker.querySelector("select");
    const search = picker.querySelector("[data-essential-spell-search]");
    const optionsContainer = picker.querySelector("[data-essential-spell-options]");

    function renderOptions() {
      const query = search.value.trim().toLocaleLowerCase();
      const options = Array.from(select.options)
        .filter((option) => option.value && !option.disabled)
        .filter((option) => !query || option.text.toLocaleLowerCase().includes(query))
        .slice(0, 8);
      optionsContainer.replaceChildren();
      optionsContainer.hidden = options.length === 0;
      options.forEach((option) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "list-group-item list-group-item-action";
        button.textContent = option.text;
        button.addEventListener("click", () => {
          setValue(select, option.value);
          search.value = option.text;
          optionsContainer.hidden = true;
        });
        optionsContainer.append(button);
      });
    }

    function syncSearch() {
      search.value = select.value ? select.selectedOptions[0]?.text || "" : "";
      optionsContainer.hidden = true;
    }

    search.addEventListener("input", renderOptions);
    search.addEventListener("focus", renderOptions);
    search.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        syncSearch();
        search.blur();
      }
    });
    select.addEventListener("change", syncSearch);
    select.addEventListener("essential:spell-options-updated", () => {
      if (document.activeElement === search) renderOptions();
    });
    document.addEventListener("click", (event) => {
      if (!picker.contains(event.target)) optionsContainer.hidden = true;
    });
    syncSearch();
  }

  const randomizers = {
    concept: randomizeConcept,
    attributes: () => randomizeRanks([3, 2, 2, 1, 1, 1, 0, 0]),
    marks: randomizeMarks,
    skills: () => randomizeRanks([3, 2, 2, 2, 1, 1, 1, 1, 1]),
    equipment: randomizeEquipment,
    supernatural: randomizeSupernatural,
  };

  wizard.addEventListener("htmx:beforeRequest", (event) => {
    if (!event.target.matches(".essential-wizard-fields-marks select, .essential-wizard-fields-equipment select, .essential-wizard-fields-supernatural select")) return;
    document.querySelector(event.target.getAttribute("hx-target"))?.classList.add("is-loading");
  });

  wizard.addEventListener("htmx:afterRequest", (event) => {
    if (!event.target.matches(".essential-wizard-fields-marks select, .essential-wizard-fields-equipment select, .essential-wizard-fields-supernatural select")) return;
    const summary = document.querySelector(event.target.getAttribute("hx-target"));
    summary?.classList.remove("is-loading");
    if (summary && !event.detail.successful) {
      summary.querySelector(".card-body").innerHTML =
        `<p class="text-danger mb-0">${summary.dataset.errorMessage}</p>`;
    }
  });

  wizard.querySelector("[data-essential-randomize]")?.addEventListener("click", () => {
    randomizers[wizard.dataset.step]?.();
  });

  wizard.addEventListener("change", (event) => {
    if (event.target.matches("input.essential-rank-input")) renderCircles();
    if (event.target.matches('[name*="-magic_aspect_"]')) updateSpellOptions();
    if (event.target.matches('[name*="-spell_"]')) updateSpellOptions();
  });
  wizard.querySelectorAll("[data-essential-item-picker]").forEach(initializeItemPicker);
  wizard.querySelectorAll("[data-essential-spell-picker]").forEach(initializeSpellPicker);
  updateSpellOptions();
  renderCircles();
});
