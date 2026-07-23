document.addEventListener("DOMContentLoaded", function () {
    let body = $("body");

    body.on("click", ".campaign-link", function (e) {
        let elem = $(this);
        let text = elem.find(".invite-text");
        let icon = elem.find(".invite-icon");
        let origText = text.data("original-text") || text.text();
        let origIcon = icon.data("original-icon") || icon.attr("class");

        e.preventDefault();
        copyTextToClipboard(elem.attr("href"));

        clearTimeout(elem.data("feedback-timeout"));
        text.data("original-text", origText);
        icon.data("original-icon", origIcon);
        text.text(elem.data("msg"));
        icon.attr("class", "fas fa-check invite-icon");
        elem.removeClass("btn-outline-primary").addClass("btn-success");

        Toast.setPlacement(TOAST_PLACEMENT.BOTTOM_LEFT);
        Toast.setMaxCount(5);
        Toast.create({
            title: elem.data("title"),
            message: elem.data("msg"),
            status: TOAST_STATUS.SUCCESS,
            timeout: 5000,
        });

        elem.data(
            "feedback-timeout",
            setTimeout(() => {
                text.text(origText);
                icon.attr("class", origIcon);
                elem.removeClass("btn-success").addClass("btn-outline-primary");
            }, 2500),
        );

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
