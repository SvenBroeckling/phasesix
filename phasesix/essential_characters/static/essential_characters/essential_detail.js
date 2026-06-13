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
