import { dispatch } from "./common.js";

document.addEventListener("click", (event) => {
    let postTrigger = event.target.closest("[data-post-trigger-url]");
    if (postTrigger) {
        let eventType = postTrigger.dataset.postTriggerEvent || "click";
        if (eventType === event.type) {
            event.preventDefault();

            const url = postTrigger.dataset.postTriggerUrl;
            const refreshAfter = postTrigger.dataset.postTriggerRefreshAfter;
            const eventAfter = postTrigger.dataset.postTriggerEventAfter;

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
                            `data-post-trigger: Failed post to ${url}`,
                        );
                    }
                });
            }
        }
    }
});
