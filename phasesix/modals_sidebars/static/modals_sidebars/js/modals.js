class SiteModal {
    constructor() {
        this.modalElement = document.getElementById("site-modal");
        this.modal = new bootstrap.Modal(this.modalElement);
        this.targetName = "body";
        this.setupGlobalListeners();
    }

    get title() {
        return this.modalElement.querySelector(".modal-title").innerHTML;
    }

    set title(title) {
        this.modalElement.querySelector(".modal-title").innerHTML = title;
    }

    get target() {
        let name = ".";

        if (this.targetName === "modal") {
            name += "modal";
        } else {
            name += "modal-" + this.targetName;
        }

        return name;
    }

    set target(target) {
        this.targetName = target;
    }

    get body() {
        return this.modalElement.querySelector(this.target).innerHTML;
    }

    set body(body) {
        this.modalElement.querySelector(this.target).innerHTML = body;
        htmx.process(this.modalElement.querySelector(this.target));
        if (this.eventShow) {
            document.dispatchEvent(
                new CustomEvent(this.eventShow, {
                    detail: this.eventShowDetail || null,
                    bubbles: true,
                }),
            );
        }
    }

    set dialog_class(value) {
        this.modalElement.querySelector(".modal-dialog").classList.add(value);
    }

    set dialog_class_name(value) {
        this.modalElement.querySelector(".modal-dialog").className += value;
    }

    setupGlobalListeners() {
        document.addEventListener("click", (e) => {
            let modalTrigger = e.target.closest("[data-modal-url]");
            if (modalTrigger) {
                this.fillModalFromDataSet(modalTrigger.dataset);
                e.preventDefault();
                this.modal.show();
            }
        });

        // clear modal when hide
        this.modalElement.addEventListener("hide.bs.modal", (event) => {
            if (this.confirmClose) {
                if (!confirm(this.confirmClose)) {
                    event.preventDefault();
                    return;
                }
            }

            if (this.htmxTriggersClose) {
                for (let t of this.htmxTriggersClose.split(",")) {
                    htmx.trigger(document.body, t);
                }
            }

            if (this.eventClose) {
                document.dispatchEvent(
                    new CustomEvent(this.eventClose, {
                        detail: this.eventCloseDetail || null,
                        bubbles: true,
                    }),
                );
                event.preventDefault();
                return false;
            }

            this.modalElement.innerHTML = "";
            let temp = document.querySelector("[data-modal-template]");
            if (temp) {
                let clon = temp.content.cloneNode(true);
                this.modalElement.appendChild(clon);
            }
            this.targetName = "body";

            if (this.refreshAfter) {
                setTimeout(() => {
                    // strip the auto show query string from the url, keeping the rest of the query string
                    let url = window.location.href.replace(
                        "?" + this.autoShowQueryString,
                        "",
                    );
                    window.location.href = url;
                }, 0);
            }

            if (this.eventAfter) {
                document.dispatchEvent(
                    new CustomEvent(this.eventAfter, {
                        detail: this.eventAfterDetail || null,
                        bubbles: true,
                    }),
                );
            }
        });

        document.addEventListener("modal-show", (event) => {
            this.modal.show();
        });

        document.addEventListener("modal-fetch-and-show", (event) => {
            this.fillModalFromDataSet(event.detail);
            this.modal.show();
        });

        document.addEventListener("modal-hide", (event) => {
            this.modal.hide();
        });

        document.addEventListener("modal-close", (event) => {
            if (event.detail && event.detail.forced) {
                delete this.eventClose;
            }
            this.modal.hide();
        });
    }

    fillModalFromDataSet(dataset) {
        if (dataset.modalTarget !== undefined) {
            this.target = dataset.modalTarget;
        }
        if (dataset.modalTitle !== undefined) {
            this.title = dataset.modalTitle;
        }
        if (dataset.modalBody) {
            this.body = dataset.modalBody;
        }
        if (dataset.modalSizeClass) {
            this.dialog_class = dataset.modalSizeClass;
        }
        if (dataset.modalClassName) {
            this.dialog_class_name = dataset.modalClassName;
        }
        if (dataset.modalBodyFromId) {
            this.body = document.querySelector(
                dataset.modalBodyFromId,
            ).innerHTML;
        }
        if (dataset.modalUrl) {
            this.url = dataset.modalUrl;

            if (dataset.modalIframe) {
                this.body = `<iframe style="width: 100%; height: 100%" src="${dataset.modalUrl}"></iframe>`;
            } else {
                fetch(dataset.modalUrl)
                    .then((response) => response.text())
                    .then((text) => {
                        this.body = text;
                    });
            }
        }
        this.refreshAfter = dataset.modalRefreshAfter;
        this.confirmClose = dataset.modalConfirmClose;
        this.eventShow = dataset.modalEventShow;
        this.eventAfter = dataset.modalEventAfter;
        this.eventClose = dataset.modalEventClose;
        this.htmxTriggersClose = dataset.modalHtmxTriggersClose;
        this.autoShowQueryString = dataset.modalAutoShowQueryString;

        if (dataset.modalEventShowDetail)
            this.eventShowDetail = this.parseToObject(
                dataset.modalEventShowDetail,
            );
        if (dataset.modalEventAfterDetail)
            this.eventAfterDetail = this.parseToObject(
                dataset.modalEventAfterDetail,
            );
        if (dataset.modalEventCloseDetail)
            this.eventCloseDetail = this.parseToObject(
                dataset.modalEventCloseDetail,
            );
    }

    parseToObject(input) {
        const keyValuePairs = input.split(";").map((pair) => pair.trim());
        const jsonObject = {};

        keyValuePairs.forEach((pair) => {
            const [key, value] = pair.split("=").map((part) => part.trim());
            if (key) {
                // Prüfe, ob der Wert eine Zahl ist und konvertiere sie entsprechend
                if (!isNaN(value)) {
                    jsonObject[key] = value.includes(".")
                        ? parseFloat(value)
                        : parseInt(value, 10);
                } else {
                    jsonObject[key] = value;
                }
            }
        });

        return jsonObject;
    }
}

window.addEventListener("DOMContentLoaded", (event) => {
    let siteModal = new SiteModal();
    window.siteModal = siteModal;

    let modalTrigger = document.querySelector(
        "[data-modal-auto-show-query-string]",
    );
    if (
        modalTrigger &&
        window.location.search.includes(
            modalTrigger.dataset.modalAutoShowQueryString,
        )
    ) {
        siteModal.fillModalFromDataSet(modalTrigger.dataset);
        siteModal.modal.show();
    }
});
