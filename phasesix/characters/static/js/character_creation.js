document.addEventListener("DOMContentLoaded", function () {
    let body = $("body");

    /* Extension Card selection */
    body.on(
        "click",
        "[data-app='characters'] .create-extension-card",
        function () {
            let id = $(this).data("extension-id");
            let option = $(
                `[data-app='characters'] #id_extensions > option[value=${id}]`,
            );
            let was_selected = $(this).hasClass("selected");
            if (was_selected) {
                option.prop("selected", false);
                $(this).removeClass("selected").attr("aria-pressed", "false");
            } else {
                option.prop("selected", true);
                $(this).addClass("selected").attr("aria-pressed", "true");
            }
        },
    );

    /* Character data form */
    function getCharacterCreationInfo(event) {
        let form = $(event.target).closest("form");
        let url = form.data("info-url");
        $.get(
            url,
            { field: event.target.name, value: event.target.value },
            function (data) {
                $(".description").html(data);
            },
        );
    }

    body.on(
        "change focus",
        "[data-app='characters'] form.character-data-form select",
        getCharacterCreationInfo,
    );
    body.on(
        "focus",
        "[data-app='characters'] form.character-data-form input",
        getCharacterCreationInfo,
    );

    /* Template selection */
    let debounceTimer = null;

    function displayWarnings(warnings) {
        let element = $("[data-app='characters'] .character-warnings");
        element.html("");
        if (!!warnings.length) {
            element.removeClass("d-none");
            for (let warning of warnings) {
                element.append(`<div>${warning}</div>`);
            }
        } else {
            element.addClass("d-none");
        }
    }

    body.on(
        "keyup",
        "[data-app='characters'] #id_creation_template_search_q",
        function (e) {
            let q = $(this).val();

            function updateTabs() {
                $("[data-app='characters'] .tab-pane").each(function (index) {
                    let elem = $(this);
                    let ct = elem.find(".constructed-template:not(.d-none)");
                    if (ct.length === 0) {
                        elem.addClass("d-none");
                        $(elem.data("rel")).addClass("disabled");
                    } else {
                        elem.removeClass("d-none");
                        $(elem.data("rel")).removeClass("disabled");
                    }
                    $(
                        "[data-app='characters'] a[data-bs-toggle=\"tab\"]:not(.disabled):first",
                    ).tab("show");
                });
            }

            if (debounceTimer) {
                clearTimeout(debounceTimer);
            }
            debounceTimer = setTimeout(function () {
                $("[data-app='characters'] .constructed-template").each(
                    function (index) {
                        if (
                            $(this)
                                .text()
                                .toLowerCase()
                                .search(q.toLowerCase()) > -1
                        ) {
                            $(this).removeClass("d-none");
                        } else {
                            $(this).addClass("d-none");
                        }
                    },
                );
                updateTabs();
            }, 100);
        },
    );

    body.on(
        "click",
        "[data-app='characters'] .constructed-template",
        function (e) {
            let template_div = $(this);
            let template_id = template_div.data("template-id");
            let preview_url = template_div.data("preview-url");
            if (template_div.hasClass("selected")) {
                $.post(
                    template_div.data("remove-url"),
                    { template_id: template_id },
                    function (data) {
                        if (data.status === "ok") {
                            $(".template-points").text(data.remaining_points);
                            template_div.removeClass("selected");
                            displayWarnings(data.warnings);
                            $(".character-preview").load(preview_url);
                        } else {
                            // shake
                        }
                    },
                );
            } else {
                $.post(
                    template_div.data("add-url"),
                    { template_id: template_id },
                    function (data) {
                        if (data.status === "ok") {
                            $("[data-app='characters'] .template-points").text(
                                data.remaining_points,
                            );
                            template_div.addClass("selected");
                            displayWarnings(data.warnings);
                            $(
                                "[data-app='characters'] .character-preview",
                            ).load(preview_url);
                        } else {
                            template_div.addClass("notenoughpoints");
                            $(
                                "[data-app='characters'] .template-points",
                            ).addClass("animated wobble");
                            setTimeout(function () {
                                template_div.removeClass("notenoughpoints");
                                $(
                                    "[data-app='characters'] .template-points",
                                ).removeClass("animated wobble");
                            }, 500);
                        }
                    },
                );
            }
            e.preventDefault();
            return false;
        },
    );

    body.on("change", "[data-app='characters'] #switch-preview", function () {
        if ($(this).prop("checked")) {
            $("[data-app='characters'] .template-list").addClass("d-none");
            $("[data-app='characters'] .character-preview").removeClass(
                "d-none",
            );
        } else {
            $("[data-app='characters'] .character-preview").addClass("d-none");
            $("[data-app='characters'] .template-list").removeClass("d-none");
        }
    });
});
