window.addEventListener("DOMContentLoaded", (event) => {
    // Fetch Form submit listener
    document.addEventListener("submit", (event) => {
        const form = event.target;
        const container = form.closest(".fetch-form-container");
        const close = form.dataset.fetchFormClose;
        const eventAfter = form.dataset.fetchFormEventAfter;
        const eventAfterDetail = form.dataset.fetchFormEventAfterDetail;
        const eventOnRender = form.dataset.fetchFormEventOnRender;

        function add_class(selector, className) {
            let elem = form.querySelector(selector);
            if (elem) {
                elem.classList.add(className);
            }
        }

        function remove_class(selector, className) {
            let elem = form.querySelector(selector);
            if (elem) {
                elem.classList.remove(className);
            }
        }

        function setButtonState(state = "enabled") {
            if (state === "enabled") {
                add_class(".form-submit-spinner", "d-none");
                add_class('[type="submit"]', "disabled");
            } else {
                remove_class(".form-submit-spinner", "d-none");
                remove_class('[type="submit"]', "disabled");
            }
        }

        if (form.dataset.fetchForm) {
            event.preventDefault();
            setButtonState("disabled");

            const formData = new FormData(form);
            if (formData.has("image-clear")) {
                formData.delete("image");
            } else {
                if (form._UploadImageBlob) {
                    formData.set("image", form._UploadImageBlob);
                }
            }

            fetch(form.getAttribute("action"), {
                method: "POST",
                body: formData,
                redirect: "manual",
                headers: {
                    mode: "same-origin",
                    "X-CSRFToken":
                        document.querySelector("body").dataset.csrfToken,
                },
            })
                .then((response) => {
                    if (response.status === 302 || response.status === 0) {
                        // Django View success_url redirect
                        return null;
                    }
                    return response.text();
                })
                .then((text) => {
                    if (text === null || text === "") {
                        if (close === "all") {
                            document.dispatchEvent(
                                new Event("sidebar-right-close"),
                            );
                            document.dispatchEvent(new Event("modal-close"));
                        }
                        if (close === "sidebar") {
                            document.dispatchEvent(
                                new Event("sidebar-right-close"),
                            );
                        } else if (close === "modal") {
                            document.dispatchEvent(new Event("modal-close"));
                        }
                        setButtonState("enabled");

                        if (eventAfter) {
                            document.dispatchEvent(
                                new CustomEvent(eventAfter, {
                                    detail: eventAfterDetail || null,
                                    bubbles: true,
                                }),
                            );
                        }
                    } else {
                        container.innerHTML = text;
                        if (eventOnRender) {
                            document.dispatchEvent(
                                new CustomEvent(eventOnRender, {
                                    detail: null,
                                    bubbles: true,
                                }),
                            );
                        }
                    }
                });
            event.preventDefault();
        }
    });
});
