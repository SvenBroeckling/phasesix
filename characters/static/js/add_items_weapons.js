$(function () {
    let timer = null

    function updateMasonry() {
        $('.modal-body div.tab-pane.active .masonry-container').masonry({percentPosition: true})
    }

    function updateTabs() {
        $('.add-item-tab-pane').each(function(index){
            let elem = $(this)
            let ct = elem.find('.add-item-card:not(.d-none)')

            if (ct.length === 0) {
                elem.addClass('d-none')
                $(elem.data('rel')).addClass('d-none')
            } else {
                elem.removeClass('d-none')
                $(elem.data('rel')).removeClass('d-none')
                $('li.add-item-nav-item:not(.d-none):first').find('a').tab('show')
            }
        })
    }

    $('.search-items-input').on('keyup', function(e){
        let q = $(this).val()

        if (timer) clearTimeout(timer)

        timer = setTimeout(function(){
            $('.add-item-card').each(function(index){
                if ($(this).text().toLowerCase().search(q.toLowerCase()) > -1) {
                    $(this).removeClass('d-none')
                } else {
                    $(this).addClass('d-none')
                }
            })
            updateTabs()
            updateMasonry()
        }, 10)

    })

    $('.add-item-nav-item').on('click', function() {
        $('#add-item-mobile-nav').collapse('hide')
        $('.btn-add-item-mobile-nav-toggle').text($(this).find('a').text())
    })
    $('.modal-body a.nav-link').first().addClass('active')
    $('.modal-body div.tab-pane').first().addClass('active')
    updateMasonry()
})
