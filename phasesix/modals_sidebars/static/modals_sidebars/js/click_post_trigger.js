window.addEventListener("load", (event) => {
    document.addEventListener("click", (event) => {
        let postTrigger = event.target.closest("[data-post-trigger]");
        if (postTrigger) {
            let eventType = postTrigger.dataset.postTriggerEvent || "click";
            if (eventType === event.type) {
                event.preventDefault();

                const url = postTrigger.dataset.postTriggerUrl;
                const refreshAfter =
                    postTrigger.dataset.postTriggerRefreshAfter;
                const fetchAfter = postTrigger.dataset.postTriggerFetchAfter;
                const fetchAfterTarget =
                    postTrigger.dataset.postTriggerFetchAfterTarget;
                const fetchAfterTitle =
                    postTrigger.dataset.postTriggerFetchAfterTitle;

                if (url) {
                    fetch(url, {
                        method: "POST",
                        redirect: "manual",
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
                                                    sidebarTitle:
                                                        fetchAfterTitle,
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
                                                    siteModalTitle:
                                                        fetchAfterTitle,
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
        }
    });
});
