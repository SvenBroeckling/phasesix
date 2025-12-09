$(function () {
    let body = $("body");

    document.addEventListener("DOMContentLoaded", function () {
        let characterMainNav = $("[data-app='characters'] .character-main-nav");
        if (characterMainNav) {
            characterMainNav.find("a[href]:first").tab("show");
        }
    });

    body.on("click", ".status-effect-description-button", function (e) {
        let elem = $(this);
        let target = elem.closest("li").find(".status-effect-description");
        if (target.hasClass("d-none")) {
            target.removeClass("d-none");
        } else {
            target.addClass("d-none");
        }
        e.preventDefault();
        return false;
    });

    body.on("click", "[data-app='characters'] .delete-character", function (e) {
        let elem = $(this);
        if (confirm(elem.data("message"))) {
            $.post(elem.attr("href"), function (data) {
                window.location = data.url;
            });
        }
        e.preventDefault();
        return false;
    });

    // Sortable Items
    document.addEventListener("attach-sortables", function () {
        $("[data-app='characters'] .item-sortable")
            .sortable({
                tolerance: "pointer",
                items: "div.card",
                placeholder:
                    '<div class="card mb-3"><div class="card-header">&nbsp;</div></div>',
            })
            .bind("sortupdate", function (e, ui) {
                let order = {};
                $("[data-app='characters'] .item-sortable > div").each(
                    (idx, e) => {
                        order[$(e).data("pk")] = idx;
                    },
                );
                $.post($(this).data("url"), order);
            });
    });
});
