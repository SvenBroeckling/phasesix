import { dispatch } from "./common.js";

const actionTriggerListener = (event) => {
    let actionTrigger = event.target.closest("[data-action-trigger-url]");
    if (actionTrigger) {
        if (
            event.type === actionTrigger.dataset.actionTriggerEvent ||
            "click"
        ) {
            event.preventDefault();

            const url = actionTrigger.dataset.actionTriggerUrl;
            const eventAfter = actionTrigger.dataset.actionTriggerEventAfter;
            const method = actionTrigger.dataset.actionTriggerMethod || "POST";

            fetch(url, {
                method: method.toUpperCase(),
                redirect: "manual",
                headers: {
                    mode: "same-origin",
                    "X-CSRFToken":
                        document.querySelector("body").dataset.csrfToken,
                },
            }).then((response) => {
                dispatch(eventAfter);
            });
        }
    }
};

document.addEventListener("click", actionTriggerListener);
document.addEventListener("change", actionTriggerListener);
