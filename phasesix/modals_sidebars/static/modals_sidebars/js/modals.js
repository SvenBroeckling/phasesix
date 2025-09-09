import { dispatch } from "./common.js";

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
        dispatch(this.eventShow);
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

        // clear the modal body when the modal is hidden
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

            this.modalElement.innerHTML = "";
            let temp = document.querySelector("[data-site-modal-template]");
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

            dispatch(this.eventAfter);
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
        this.htmxTriggersClose = dataset.modalHtmxTriggersClose;
        this.autoShowQueryString = dataset.modalAutoShowQueryString;
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
