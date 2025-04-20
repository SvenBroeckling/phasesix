$(document).ready(function () {
    return; // disable for now

    let body = document.querySelector("body");
    window.eventSource = new EventSource(body.dataset.eventSourceUrl);
    window.addEventListener("beforeunload", function () {
        window.eventSource.close();
    });
    window.addEventListener("pageshow", function (event) {
        if (event.persisted) {
            location.reload()
        }
    });

    function register(eventName, cb) {
        window.eventSource.addEventListener(eventName, cb);
    }
})
