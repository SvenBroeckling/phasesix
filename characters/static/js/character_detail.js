$(function () {
    let body = $('body')

    body.on("click", ".status-effect-description-button", function (e) {
        let elem = $(this);
        let target = elem.closest("li").find('.status-effect-description');
        if (target.hasClass('d-none')) {
            target.removeClass('d-none');
        } else {
            target.addClass('d-none');
        }
        e.preventDefault()
        return false

    })

    body.on('click', '.delete-character', function (e) {
        let elem = $(this)
        if (confirm(elem.data('message'))) {
            $.post(elem.attr('href'), function (data) {
                window.location = data.url
            })
        }
        e.preventDefault()
        return false
    })

    // Sortable Items
    function saveSortOrder(selector, url) {
        let order = {}
        $(selector).each((idx, e) => {
            order[$(e).data('pk')] = idx
        })
        $.post(url, order)
    }

    for (const element of [".item-sortable"]) {
        $(element).sortable({
            tolerance: 'pointer',
            items: 'div.card',
            placeholder: '<div class="card mb-3"><div class="card-header">&nbsp;</div></div>'
        }).bind('sortstart', function (e, ui) {
        }).bind('sortstop', function (e, ui) {
        }).bind('sortupdate', function (e, ui) {
            saveSortOrder(`${element} > div`, $(this).data('url'))
        })
    }

    // save bootstrap tabs
    $('a[data-bs-toggle="tab"]').on('click', function (e) {
        window.localStorage.setItem('activeTab', $(e.target).attr('href'))
    })

    var activeTab = window.localStorage.getItem('activeTab')
    if (activeTab) {
        $('a[href="' + activeTab + '"]').tab('show')
    }

    $('[data-bs-toggle="popover"]').popover()
    $('.template').tilt({glare: false, perspective: 1800})

    setTimeout(() => $('.masonry-container').masonry({percentPosition: true}), 500)
    body.on('click', 'a[data-bs-toggle="tab"]', function (e) {
        let target = $(e.target).closest('a[data-bs-toggle="tab"]').attr('data-bs-target')
        if (target) {
            $(target).find('.masonry-container').masonry({percentPosition: true})
        }
    })
})
