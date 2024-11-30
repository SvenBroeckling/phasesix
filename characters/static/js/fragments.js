let timeout = null;

function refresh_fragments() {
    function refresh() {
        $('.fragment').each(function (index) {
            let active_href = $(".character-main-nav").find(".active").attr("href")

            $(this).load($(this).data('fragment-url'), function (response, status, xhr) {
                $(this).children(':first').unwrap() // keep the original fragment container
                $('[data-bs-toggle="popover"]').popover()
                $('.masonry-container').masonry({percentPosition: true})
                if (active_href !== undefined) {  // set the prior active tab in the character nav
                    $('.character-main-nav a[href="' + active_href + '"]').tab('show')
                }
            })
        })

        let sc = $('.sidebar-content')
        if (sc.data('sidebar-url') !== undefined) {
            sc.load(sc.data('sidebar-url'), (response, status, xhr) => {
                if (xhr.status === 404) {
                    $('#sidebar-right').css('width', '');
                }
            })
        }
    }

    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(refresh, 500)
}