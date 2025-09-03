window.addEventListener("load", (event) => {
    // Field on change post trigger listener
    addEventListener("change", (event) => {
        const element = event.target;
        if (element.dataset.postTrigger) {
            let eventType = element.dataset.postTriggerEvent || "click";
            if (event.type === eventType) {
                const refreshAfter = element.dataset.postTriggerRefreshAfter;
                const fetchAfter = element.dataset.postTriggerFetchAfter;
                const fetchAfterTarget =
                    element.dataset.postTriggerFetchAfterTarget;
                const fetchAfterTitle =
                    element.dataset.postTriggerFetchAfterTitle;

                const formData = new FormData();
                formData.append(element.getAttribute("name"), element.value);

                fetch(element.dataset.postTriggerUrl, {
                    method: "POST",
                    body: formData,
                    redirect: "manual", // manual redirect to catch django form success_url redirects
                    headers: {
                        mode: "same-origin",
                        "X-CSRFToken": csrftoken,
                    },
                }).then((response) => {
                    if (refreshAfter) {
                        window.location.reload();
                    } else if (
                        response.status === 200 ||
                        response.status === 302
                    ) {
                        if (fetchAfter) {
                            if (
                                fetchAfterTarget &&
                                fetchAfterTarget === "sidebar"
                            ) {
                                document.dispatchEvent(
                                    new CustomEvent(
                                        "sidebar-right-fetch-and-show",
                                        {
                                            detail: {
                                                sidebarTitle: fetchAfterTitle,
                                                sidebarUrl: fetchAfter,
                                            },
                                        },
                                    ),
                                );
                            } else if (
                                fetchAfterTarget &&
                                fetchAfterTarget === "modal"
                            ) {
                                document.dispatchEvent(
                                    new CustomEvent(
                                        "site-modal-fetch-and-show",
                                        {
                                            detail: {
                                                siteModalTitle: fetchAfterTitle,
                                                siteModalUrl: fetchAfter,
                                            },
                                        },
                                    ),
                                );
                            } else {
                                fetch(fetchAfter, { method: "GET" })
                                    .then((response) => response.text())
                                    .then((text) => {
                                        if (fetchAfterTarget) {
                                            document.querySelector(
                                                fetchAfterTarget,
                                            ).innerHTML = text;
                                        }
                                    });
                            }
                        }
                    } else {
                        console.error(
                            `data-post-trigger: Failed post to ${url}`,
                        );
                    }
                });
            }
        }
    });
});
