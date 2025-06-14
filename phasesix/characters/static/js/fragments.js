let timeout = null;

let fragmentsVisible = ["description", "dramaturgy"];

function refresh_fragments() {
    function refresh() {
        $(".fragment").each(function (index) {
            const fragmentTemplate = $(this).data("fragment-template");
            const navHref = $(".character-main-nav")
                .find(".active")
                .attr("href");

            if (
                !fragmentsVisible.includes(fragmentTemplate) &&
                fragmentTemplate !== "status"
            )
                return;

            $(this).load(
                $(this).data("fragment-url"),
                function (response, status, xhr) {
                    $(this).children(":first").unwrap(); // keep the original fragment container
                    $('[data-bs-toggle="popover"]').popover();
                    // set the prior active tab in the character nav
                    if (navHref) {
                        $(`.character-main-nav a[href="${navHref}"]`).tab(
                            "show",
                        );
                    }
                },
            );
        });

        let sc = $(".sidebar-content");
        if (sc.data("sidebar-url") !== undefined) {
            sc.load(sc.data("sidebar-url"), (response, status, xhr) => {
                if (xhr.status === 404) {
                    $("#sidebar-right").css("width", "");
                }
            });
        }
    }

    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(refresh, 500);
}

document.addEventListener("DOMContentLoaded", () => {
    refresh_fragments();
    document.addEventListener("refresh-fragment", (e) => {
        fragmentsVisible = [e.detail.fragment_template];
        refresh_fragments();
    });
});
