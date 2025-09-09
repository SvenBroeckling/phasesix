import { dispatch } from "./common.js";

document.addEventListener("click", (event) => {
    let actionTrigger = event.target.closest("[data-action-trigger-url]");
    if (actionTrigger) {
        let eventType = actionTrigger.dataset.actionTriggerEvent || "click";
        if (eventType === event.type) {
            event.preventDefault();

            const url = actionTrigger.dataset.actionTriggerUrl;
            const refreshAfter =
                actionTrigger.dataset.actionTriggerRefreshAfter;
            const eventAfter = actionTrigger.dataset.actionTriggerEventAfter;

            if (url) {
                fetch(url, {
                    method: "POST",
                    redirect: "manual",
                    headers: {
                        mode: "same-origin",
                        "X-CSRFToken":
                            document.querySelector("body").dataset.csrfToken,
                    },
                }).then((response) => {
                    if (refreshAfter) {
                        window.location.reload();
                    } else if (
                        response.status === 200 ||
                        response.status === 302 ||
                        response.status === 0
                    ) {
                        dispatch(eventAfter);
                    } else {
                        console.error(
                            `data-action-trigger: Failed post to ${url}`,
                        );
                    }
                });
            }
        }
    }
});
