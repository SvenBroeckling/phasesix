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
    return Array.from(select.options).filter((option) => option.value && predicate(option));
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
    setValue(field("focus"), randomItem(randomText.foci));
    setValue(field("regeneration_ritual"), randomItem(randomText.rituals));

    const spellOriginsElement = document.querySelector("#essential-spell-origins");
    const spellOrigins = spellOriginsElement ? JSON.parse(spellOriginsElement.textContent) : {};
    const aspectCount = Number(wizard.dataset.aspectSlots);
    const spellCount = Number(wizard.dataset.spellSlots);
    const selectedAspects = randomizeMultipleSelect(field("magic_aspects"), aspectCount);
    randomizeMultipleSelect(
      field("spells"),
      spellCount,
      (option) => selectedAspects.includes(spellOrigins[option.value]),
    );
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
    if (!event.target.matches(".essential-wizard-fields-marks select, .essential-wizard-fields-equipment select")) return;
    document.querySelector(event.target.getAttribute("hx-target"))?.classList.add("is-loading");
  });

  wizard.addEventListener("htmx:afterRequest", (event) => {
    if (!event.target.matches(".essential-wizard-fields-marks select, .essential-wizard-fields-equipment select")) return;
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
  });
  renderCircles();
});
