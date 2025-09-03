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
            let sidebarTrigger = e.target.closest("[data-sidebar-right]");
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
        });

        // Don't break existing code. FIXME: Replace occurrences in html with -hide and remove this
        document.addEventListener("sidebar-right-close", (event) => {
            this.offcanvas.hide();
            if (this.refreshAfter) {
                window.location.reload();
            }
            if (this.eventAfter) {
                document.dispatchEvent(
                    new CustomEvent(this.eventAfter, { bubbles: true }),
                );
            }
        });
    }

    fillSidebarFromDataSet(dataset) {
        if (dataset.sidebarTitle !== undefined) {
            this.title = dataset.sidebarTitle;
        }
        if (dataset.sidebarBody) {
            this.body = dataset.sidebarBody;
        }
        if (dataset.sidebarSizeClass) {
            this.dialog_class = dataset.sidebarSizeClass;
        }
        if (dataset.sidebarBodyFromId) {
            this.body = document.querySelector(
                dataset.sidebarBodyFromId,
            ).innerHTML;
        }
        if (dataset.sidebarUrl) {
            if (dataset.sidebarIframe) {
                this.body = `<iframe style="width: 100%; height: 100%" src="${dataset.siteModalUrl}"></iframe>`;
            } else {
                fetch(dataset.sidebarUrl)
                    .then((response) => response.text())
                    .then((text) => (this.body = text));
            }
        }
        this.refreshAfter = dataset.sidebarRefreshAfter;
        this.eventAfter = dataset.sidebarEventAfter;
    }
}

window.addEventListener("DOMContentLoaded", (event) => {
    let sidebarRight = new SidebarRight();
    window.sidebarRight = sidebarRight;
});
