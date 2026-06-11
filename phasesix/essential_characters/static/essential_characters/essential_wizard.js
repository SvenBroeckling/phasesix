document.addEventListener("DOMContentLoaded", () => {
  const wizard = document.querySelector(".essential-wizard");
  if (!wizard) return;

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

  wizard.addEventListener("htmx:beforeRequest", (event) => {
    if (!event.target.matches(".essential-wizard-fields-marks select")) return;
    document.querySelector(event.target.getAttribute("hx-target"))?.classList.add("is-loading");
  });

  wizard.addEventListener("htmx:afterRequest", (event) => {
    if (!event.target.matches(".essential-wizard-fields-marks select")) return;
    const summary = document.querySelector(event.target.getAttribute("hx-target"));
    summary?.classList.remove("is-loading");
    if (summary && !event.detail.successful) {
      summary.querySelector(".card-body").innerHTML =
        `<p class="text-danger mb-0">${summary.dataset.errorMessage}</p>`;
    }
  });

  wizard.querySelector("[data-essential-randomize]")?.addEventListener("click", () => {
    const values = wizard.dataset.step === "attributes"
      ? shuffle([3, 2, 2, 1, 1, 1, 0, 0])
      : shuffle([3, 2, 2, 2, 1, 1, 1, 1, 1]);
    groups().forEach((group, index) => {
      const input = group.find((candidate) => Number(candidate.value) === values[index]);
      if (input) input.checked = true;
    });
    renderCircles();
  });

  wizard.addEventListener("change", (event) => {
    if (event.target.matches("input.essential-rank-input")) renderCircles();
  });
  renderCircles();
});
