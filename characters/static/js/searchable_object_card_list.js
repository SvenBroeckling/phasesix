$(function () {
    let timer = null


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
        })
    }

    $('.search-objects-input').on('keyup', function (e) {
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

    $('.searchable-object-card-list-nav-item').on('click', function () {
        $('#searchable-object-card-list-mobile-nav').collapse('hide')
        $('.btn-searchable-object-card-list-mobile-nav-toggle').text($(this).find('a').text())
    })
})
