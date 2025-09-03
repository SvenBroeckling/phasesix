(function () {
    $(function () {
        var $sortables = $(".sortable");
        if ($sortables.length) {
            $sortables
                .sortable({
                    connectWith: ".sortable",
                    items: "> .plot-element-container",
                    forcePlaceholderSize: true,
                    placeholder: "sortable-placeholder",
                    handle: ".plot-bar",
                })
                .on("sortupdate", function (e) {
                    var $container = $(this);
                    var order = $container
                        .children(".plot-element-container")
                        .map(function () {
                            return $(this).data("element-id");
                        })
                        .get();
                    console.log(
                        "Sorted parent",
                        $container.data("parent-id"),
                        "->",
                        order,
                    );
                });
        }

        $(document).on("click", ".toggle-children", function () {
            var $icon = $(this).find("i");
            $icon.toggleClass("fa-chevron-down fa-chevron-right");
        });
    });
})();
