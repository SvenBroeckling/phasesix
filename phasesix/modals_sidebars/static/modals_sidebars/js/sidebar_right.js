class SidebarRight {
    constructor() {
        this.sidebarElement = document.getElementById("sidebar-right");
        this.offcanvas = new bootstrap.Offcanvas(this.sidebarElement);
        this.setupGlobalListeners();
    }

    get title() {
        return this.sidebarElement.querySelector(".offcanvas-title").innerHTML;
    }

    set title(title) {
        this.sidebarElement.querySelector(".offcanvas-title").innerHTML = title;
    }

    get body() {
        return this.sidebarElement.querySelector(".offcanvas-body").innerHTML;
    }

    set body(body) {
        this.sidebarElement.querySelector(".offcanvas-body").innerHTML = body;
        htmx.process(this.sidebarElement.querySelector(".offcanvas-body"));
    }

    set dialog_class(value) {
        this.sidebarElement
            .querySelector("#sidebar-right")
            .classList.add(value);
    }

    setupGlobalListeners() {
        document.addEventListener("click", (e) => {
            let sidebarTrigger = e.target.closest("[data-sidebar-right-url]");
            if (sidebarTrigger) {
                this.fillSidebarFromDataSet(sidebarTrigger.dataset);
                e.preventDefault();
                this.offcanvas.show();
            }
        });

        document.addEventListener("sidebar-right-show", (event) => {
            this.offcanvas.show();
        });

        document.addEventListener("sidebar-right-fetch-and-show", (event) => {
            this.fillSidebarFromDataSet(event.detail);
            this.offcanvas.show();
        });

        document.addEventListener("sidebar-right-hide", (event) => {
            this.offcanvas.hide();
            if (this.refreshAfter) {
                window.location.reload();
            }
            this.#dispatch(this.eventAfter);
        });
    }

    fillSidebarFromDataSet(dataset) {
        if (dataset.sidebarRightTitle !== undefined) {
            this.title = dataset.sidebarRightTitle;
        }
        if (dataset.sidebarRightBody) {
            this.body = dataset.sidebarRightBody;
        }
        if (dataset.sidebarSizeClass) {
            this.dialog_class = dataset.sidebarRightSizeClass;
        }
        if (dataset.sidebarRightBodyFromId) {
            this.body = document.querySelector(
                dataset.sidebarRightBodyFromId,
            ).innerHTML;
        }
        if (dataset.sidebarRightUrl) {
            if (dataset.sidebarRightIframe) {
                this.body = `<iframe style="width: 100%; height: 100%" src="${dataset.sidebarRightUrl}"></iframe>`;
            } else {
                fetch(dataset.sidebarRightUrl)
                    .then((response) => response.text())
                    .then((text) => (this.body = text));
            }
        }
        this.refreshAfter = dataset.sidebarRightRefreshAfter;
        this.eventAfter = dataset.sidebarRightEventAfter;
    }

    /* eventString: comma separated string of event names to dispatch */
    #dispatch(eventString) {
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
}

window.addEventListener("DOMContentLoaded", (event) => {
    let sidebarRight = new SidebarRight();
    window.sidebarRight = sidebarRight;
});
