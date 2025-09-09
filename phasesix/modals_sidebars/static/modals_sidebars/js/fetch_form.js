window.addEventListener("DOMContentLoaded", (event) => {
    /* eventString: comma separated string of event names to dispatch */
    function dispatch(eventString) {
        if (eventString) {
            for (let e of eventString.split(",")) {
                document.dispatchEvent(
                    new CustomEvent(e, {
                        detail: null,
                        bubbles: true,
                    }),
                );
            }
        }
    }

    document.addEventListener("submit", (event) => {
        const form = event.target;
        const container = form.closest(".fetch-form-container");
        const close = form.dataset.fetchFormClose;
        const eventAfter = form.dataset.fetchFormEventAfter;
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
                        return null; // Django View success_url redirect
                    }
                    return response.text();
                })
                .then((text) => {
                    if (text === null || text === "") {
                        if (close === "all") {
                            dispatch("sidebar-right-hide,modal-hide");
                        }
                        if (close === "sidebar") {
                            dispatch("sidebar-right-hide");
                        } else if (close === "modal") {
                            dispatch("modal-hide");
                        }
                        setButtonState("enabled");
                        dispatch(eventAfter);
                    } else {
                        container.innerHTML = text;
                        dispatch(eventOnRender);
                    }
                });
            event.preventDefault();
        }
    });
});
