$(function () {
    let timer = null
    let body = $('body')


    function updateTabs() {
        $('.searchable-object-card-list-tab-pane').each(function (index) {
            let elem = $(this)
            let ct = elem.find('.searchable-object-card:not(.d-none)')

            if (ct.length === 0) {
                elem.addClass('d-none')
                $(elem.data('rel')).addClass('d-none')
            } else {
                elem.removeClass('d-none')
                $(elem.data('rel')).removeClass('d-none')
                $('li.searchable-object-card-list-nav-item:not(.d-none):first').find('a').tab('show')
            }
            setTimeout(function () {
                $(".page-modal-container .masonry-container").masonry({percentPosition: true})
            }, 200)
        })
    }

    body.on('keyup', '.search-objects-input', function (e) {
        let q = $(this).val()

        if (timer) clearTimeout(timer)

        timer = setTimeout(function () {
            $('.searchable-object-card').each(function (index) {
                if ($(this).text().toLowerCase().search(q.toLowerCase()) > -1) {
                    $(this).removeClass('d-none')
                } else {
                    $(this).addClass('d-none')
                }
            })
            updateTabs()
        }, 10)

    })

    body.on('click', '.searchable-object-card-list-nav-item', function () {
        $('#searchable-object-card-list-mobile-nav').collapse('hide')
        $('.btn-searchable-object-card-list-mobile-nav-toggle').text($(this).find('a').text())
    })
})
