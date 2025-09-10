$(function () {
    let body = $("body");

    body.on("click", "a.autotag-link", function (event) {
        let elem = $(this);
        let oldtext = elem.text();
        elem.text(elem.data("status-text"));
        elem.prop("disabled", true);

        $.post(
            elem.data("url"),
            $(".wiki_page_form").serialize(),
            function (data) {
                $("#id_text_de").text(data.text_de);
                $("#id_text_en").text(data.text_en);
                elem.text(oldtext);
                elem.prop("disabled", false);
            },
        );
        return false;
    });

    body.on("click", "a.copy-text-without-links", function (event) {
        const regex = /\[\[[^\]]+\|(.+?)\]\]/g;
        const elem = $(this);
        const language = elem.data("language");
        const field = $(`#id_text_${language}`);

        copyTextToClipboard(field.text().replace(regex, "$1"));

        const orig_text = elem.text();
        elem.text(elem.data("message"));
        setTimeout(() => elem.text(orig_text), 1000);

        event.preventDefault();
        return false;
    });

    // Sortable sub pages
    document.addEventListener("attach-sortables", function () {
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
