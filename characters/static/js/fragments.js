function refresh_fragments() {
    $('.fragment').each(function (index) {
        $(this).load($(this).data('fragment-url'), function (response, status, xhr) {
            $(this).children(':first').unwrap() // keep the original fragment container
            $('[data-bs-toggle="popover"]').popover()
            $('.masonry-container').masonry({percentPosition: true})
        })
    })

    let sc = $('.sidebar-content')
    if (sc.data('sidebar-url') !== undefined) {
        sc.load(sc.data('sidebar-url'), (response, status, xhr) => {
            if(xhr.status === 404) {
                $('#sidebar-right').css('width', '');
            }
        })
    }
}

