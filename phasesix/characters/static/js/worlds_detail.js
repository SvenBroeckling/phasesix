$(function () {
    let body = $("body");

    // Sortable sub pages
    document.addEventListener("worlds-attach-subpages-sortable", function () {
        $(".wiki-link-sortable")
            .sortable({
                tolerance: "pointer",
                items: "div.card",
                placeholder:
                    '<div class="card mb-3"><div class="card-header">&nbsp;</div></div>',
            })
            .bind("sortupdate", function (e, ui) {
                let order = {};
                $(".wiki-link-sortable > div").each((idx, e) => {
                    order[$(e).data("pk")] = idx;
                });
                $.post($(this).data("url"), order);
            });
    });
});
