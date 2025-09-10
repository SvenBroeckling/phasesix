document.addEventListener("DOMContentLoaded", function () {
    let body = $("body");

    body.on("click", "[data-app='campaigns'] .campaign-link", function (e) {
        let elem = $(this);
        let text = $(this).find(".invite-text");
        let orig_text = text.text();
        copyTextToClipboard(elem.attr("href"));

        text.text(elem.data("msg"));
        setTimeout(() => text.text(orig_text), 2000);

        e.preventDefault();
        return false;
    });

    $("[data-app='campaigns'] table.campaign-status-sortable").tablesorter({
        textExtraction: {
            ".data": function (node, table, cellIndex) {
                return $(node).find("span.sort-key").text();
            },
        },
    });

    // Campaign creation
    body.on("click", "[data-app='campaigns'] .create-epoch-card", function () {
        let id = $(this).data("extension-id");
        let option = $(`#id_extensions > option[value=${id}]`);
        let was_selected = $(this).hasClass("selected");
        if (was_selected) {
            option.removeAttr("selected");
            $(this).removeClass("selected");
        } else {
            option.attr("selected", "selected");
            $(this).addClass("selected");
        }
    });
});
