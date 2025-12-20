(function () {
    $(function () {
        function initSortable() {
            var $sortables = $(".sortable");
            if ($sortables.length) {
                try {
                    // Destroy previous instances to avoid issues
                    $sortables.each(function () {
                        try {
                            $(this).sortable("destroy");
                        } catch (e) {}
                    });

                    $sortables
                        .sortable({
                            connectWith: ".sortable",
                            items: ".plot-element-container",
                            handle: ".drag-handle",
                            placeholderClass:
                                "sortable-placeholder plot-element-container",
                            forcePlaceholderSize: true,
                            copy: false,
                        })
                        .on("sortstart", function (e, ui) {
                            $(".sortable").addClass("sortable-active");
                        })
                        .on("sortstop", function (e, ui) {
                            $(".sortable").removeClass("sortable-active");
                        })
                        .on("sortupdate", function (e, ui) {
                            var $container = $(this);
                            var order = $container
                                .children(".plot-element-container")
                                .map(function () {
                                    return $(this).data("element-id");
                                })
                                .get();

                            var parentId = $container.data("parent-id");
                            var reorderUrl = $container.data("reorder-url");

                            if (reorderUrl && order.length > 0) {
                                $.post(reorderUrl, {
                                    parent_id: parentId,
                                    element_ids: order,
                                })
                                    .done(function (response) {})
                                    .fail(function (xhr) {
                                        console.error(
                                            "Reorder failed",
                                            xhr.responseText,
                                        );
                                    });
                            }
                        });
                } catch (e) {
                    console.error("Error initializing sortable:", e);
                }
            }
        }

        initSortable();

        $(document).on("click", ".toggle-children", function () {
            var $icon = $(this).find("i");
            $icon.toggleClass("fa-chevron-down fa-chevron-right");
        });

        const STORAGE_KEY = "openPlotElements";

        function getOpenIds() {
            try {
                return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
            } catch (e) {
                return [];
            }
        }

        function saveOpenId(id) {
            let ids = getOpenIds();
            if (!ids.includes(id)) {
                ids.push(id);
                localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
            }
        }

        function removeOpenId(id) {
            let ids = getOpenIds();
            const index = ids.indexOf(id);
            if (index > -1) {
                ids.splice(index, 1);
                localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
            }
        }

        function restoreCollapseState($container) {
            const openIds = getOpenIds();
            openIds.forEach(function (id) {
                const $el = $container
                    ? $container.find("#" + id)
                    : $("#" + id);
                if ($el.length && $el.hasClass("collapse")) {
                    $el.addClass("show");
                    $('[data-bs-target="#' + id + '"]').attr(
                        "aria-expanded",
                        "true",
                    );
                }
            });
        }

        // Initial restoration
        restoreCollapseState();

        // Listen for collapse events to update localStorage
        $(document).on("shown.bs.collapse", ".collapse", function () {
            if (this.id && this.id.startsWith("details-")) {
                saveOpenId(this.id);
            }
        });

        $(document).on("hidden.bs.collapse", ".collapse", function () {
            if (this.id && this.id.startsWith("details-")) {
                // If the element is no longer in the document, it was removed by HTMX, not closed by the user.
                if (!document.body.contains(this)) return;
                removeOpenId(this.id);
            }
        });

        // Restore state after HTMX swaps
        document.addEventListener("htmx:afterSettle", function (evt) {
            // Check if the request was for a plot fragment
            const url = (evt.detail.xhr && evt.detail.xhr.responseURL) || "";
            if (url.indexOf("xhr_plot_fragment") !== -1) {
                restoreCollapseState();
                initSortable();
            }
        });
    });
})();
