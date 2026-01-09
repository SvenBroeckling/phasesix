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

        function setPlotMode($scope, mode) {
            var isEdit = mode === "edit";
            $scope.find('[data-plot-mode="view"]').toggleClass("d-none", isEdit);
            $scope.find('[data-plot-mode="edit"]').toggleClass("d-none", !isEdit);
            var $toggle = $scope.find("[data-plot-mode-toggle]");
            if ($toggle.length) {
                $toggle.prop("checked", isEdit);
            }
            if (isEdit) {
                restoreCollapseState($scope.find('[data-plot-mode="edit"]'));
                initSortable();
            }
        }

        function initPlotModeToggles() {
            $("[data-plot-mode-scope]").each(function () {
                var $scope = $(this);
                var $toggle = $scope.find("[data-plot-mode-toggle]");
                if (!$toggle.length) {
                    return;
                }

                var storageKey = $toggle.attr("data-plot-mode-storage-key");
                var saved =
                    storageKey && localStorage.getItem(storageKey)
                        ? localStorage.getItem(storageKey)
                        : null;
                var mode = saved === "edit" || saved === "view" ? saved : "view";
                setPlotMode($scope, mode);

            });
        }

        initSortable();
        initPlotModeToggles();

        $(document).on("change.plotMode", "[data-plot-mode-toggle]", function () {
            var $toggle = $(this);
            var $scope = $toggle.closest("[data-plot-mode-scope]");
            if (!$scope.length) {
                return;
            }
            var storageKey = $toggle.attr("data-plot-mode-storage-key");
            var nextMode = this.checked ? "edit" : "view";
            setPlotMode($scope, nextMode);
            if (storageKey) {
                localStorage.setItem(storageKey, nextMode);
            }
        });

        $(document).on("click", ".toggle-children", function () {
            var $icon = $(this).find("i");
            $icon.toggleClass("fa-chevron-down fa-chevron-right");
        });

        const STORAGE_KEY = "openPlotElements";
        const CHILDREN_STORAGE_KEY = "collapsedPlotViewerChildren";

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

        function getCollapsedChildrenIds() {
            try {
                return (
                    JSON.parse(localStorage.getItem(CHILDREN_STORAGE_KEY)) || []
                );
            } catch (e) {
                return [];
            }
        }

        function saveCollapsedChildrenId(id) {
            let ids = getCollapsedChildrenIds();
            if (!ids.includes(id)) {
                ids.push(id);
                localStorage.setItem(CHILDREN_STORAGE_KEY, JSON.stringify(ids));
            }
        }

        function removeCollapsedChildrenId(id) {
            let ids = getCollapsedChildrenIds();
            const index = ids.indexOf(id);
            if (index > -1) {
                ids.splice(index, 1);
                localStorage.setItem(CHILDREN_STORAGE_KEY, JSON.stringify(ids));
            }
        }

        function restoreChildrenCollapseState($container) {
            const collapsedIds = getCollapsedChildrenIds();
            const $collapses = $container
                ? $container.find("[data-plot-children-collapse]")
                : $("[data-plot-children-collapse]");
            $collapses.each(function () {
                var $el = $(this);
                if (!$el.attr("id")) {
                    return;
                }
                var isCollapsed = collapsedIds.includes($el.attr("id"));
                if (isCollapsed) {
                    $el.removeClass("show");
                    $('[data-bs-target="#' + $el.attr("id") + '"]').attr(
                        "aria-expanded",
                        "false",
                    );
                } else {
                    $el.addClass("show");
                    $('[data-bs-target="#' + $el.attr("id") + '"]').attr(
                        "aria-expanded",
                        "true",
                    );
                }
            });
            syncChildrenToggleIcons($container);
        }

        function syncChildrenToggleIcons($container) {
            var $targets = $container
                ? $container.find("[data-plot-children-toggle]")
                : $("[data-plot-children-toggle]");
            $targets.each(function () {
                var $toggle = $(this);
                var targetId = $toggle.attr("data-bs-target");
                if (!targetId) {
                    return;
                }
                var $collapse = $(targetId);
                var $icon = $toggle.find("i");
                if (!$icon.length) {
                    return;
                }
                if ($collapse.hasClass("show")) {
                    $icon
                        .removeClass("fa-chevron-right")
                        .addClass("fa-chevron-down");
                } else {
                    $icon
                        .removeClass("fa-chevron-down")
                        .addClass("fa-chevron-right");
                }
            });
        }

        // Initial restoration
        restoreCollapseState();
        restoreChildrenCollapseState();

        // Listen for collapse events to update localStorage
        $(document).on("shown.bs.collapse", ".collapse", function () {
            if (this.id && this.id.startsWith("details-")) {
                saveOpenId(this.id);
            } else if ($(this).is("[data-plot-children-collapse]")) {
                removeCollapsedChildrenId(this.id);
                syncChildrenToggleIcons();
            }
        });

        $(document).on("hidden.bs.collapse", ".collapse", function () {
            if (this.id && this.id.startsWith("details-")) {
                // If the element is no longer in the document, it was removed by HTMX, not closed by the user.
                if (!document.body.contains(this)) return;
                removeOpenId(this.id);
            } else if ($(this).is("[data-plot-children-collapse]")) {
                if (!document.body.contains(this)) return;
                saveCollapsedChildrenId(this.id);
                syncChildrenToggleIcons();
            }
        });

        // Restore state after HTMX swaps
        document.addEventListener("htmx:afterSettle", function (evt) {
            // Check if the request was for a plot fragment
            const url = (evt.detail.xhr && evt.detail.xhr.responseURL) || "";
            if (url.indexOf("xhr_plot_fragment") !== -1) {
                if (evt.detail && evt.detail.target) {
                    restoreCollapseState($(evt.detail.target));
                    restoreChildrenCollapseState($(evt.detail.target));
                } else {
                    restoreCollapseState();
                    restoreChildrenCollapseState();
                }
                initSortable();
            }
            if (url.indexOf("xhr_campaign_plot_view") !== -1) {
                if (evt.detail && evt.detail.target) {
                    restoreCollapseState($(evt.detail.target));
                    restoreChildrenCollapseState($(evt.detail.target));
                } else {
                    restoreCollapseState();
                    restoreChildrenCollapseState();
                }
            }
            if (evt.detail && evt.detail.target) {
                var $target = $(evt.detail.target);
                if ($target.find("[data-plot-children-collapse]").length) {
                    restoreChildrenCollapseState($target);
                }
                if ($target.find('[data-bs-target^="#details-"]').length) {
                    restoreCollapseState($target);
                }
            }
            initPlotModeToggles();
        });

        document.addEventListener("htmx:afterSwap", function (evt) {
            if (evt.detail && evt.detail.target) {
                var $target = $(evt.detail.target);
                if ($target.find("[data-plot-children-collapse]").length) {
                    restoreChildrenCollapseState($target);
                }
            }
        });
    });
})();
