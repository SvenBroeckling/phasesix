(function () {
    $(function () {
        function getStorageKey(container) {
            if (!container) {
                return null;
            }
            return container.dataset.campaignPlotStorageKey || null;
        }

        function getOpenIds(storageKey) {
            if (!storageKey) {
                return [];
            }
            try {
                return JSON.parse(localStorage.getItem(storageKey)) || [];
            } catch (e) {
                return [];
            }
        }

        function saveOpenId(storageKey, id) {
            if (!storageKey) {
                return;
            }
            let ids = getOpenIds(storageKey);
            if (!ids.includes(id)) {
                ids.push(id);
                localStorage.setItem(storageKey, JSON.stringify(ids));
            }
        }

        function removeOpenId(storageKey, id) {
            if (!storageKey) {
                return;
            }
            let ids = getOpenIds(storageKey);
            const index = ids.indexOf(id);
            if (index > -1) {
                ids.splice(index, 1);
                localStorage.setItem(storageKey, JSON.stringify(ids));
            }
        }

        function restoreCollapseState($root) {
            if (!$root || !$root.length) {
                return;
            }
            const storageKey = getStorageKey($root[0]);
            const openIds = getOpenIds(storageKey);
            openIds.forEach(function (id) {
                const $el = $root.find("#" + id);
                if ($el.length && $el.hasClass("collapse")) {
                    $el.addClass("show");
                    $root
                        .find('[data-bs-target="#' + id + '"]')
                        .attr("aria-expanded", "true");
                }
            });
        }

        $("[data-campaign-plot-storage-key]").each(function () {
            restoreCollapseState($(this));
        });

        $(document).on("shown.bs.collapse", ".collapse", function () {
            if (this.id && this.id.startsWith("details-")) {
                const container = this.closest(
                    "[data-campaign-plot-storage-key]",
                );
                const storageKey = getStorageKey(container);
                saveOpenId(storageKey, this.id);
            }
        });

        $(document).on("hidden.bs.collapse", ".collapse", function () {
            if (this.id && this.id.startsWith("details-")) {
                if (!document.body.contains(this)) return;
                const container = this.closest(
                    "[data-campaign-plot-storage-key]",
                );
                const storageKey = getStorageKey(container);
                removeOpenId(storageKey, this.id);
            }
        });

        document.addEventListener("htmx:afterSettle", function (evt) {
            const url = (evt.detail.xhr && evt.detail.xhr.responseURL) || "";
            if (url.indexOf("xhr_campaign_fragment") !== -1) {
                $("[data-campaign-plot-storage-key]").each(function () {
                    restoreCollapseState($(this));
                });
            }
        });
    });
})();
