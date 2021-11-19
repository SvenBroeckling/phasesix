$(function () {
    let body = $('body')

    // helper
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
            sc.load(sc.data('sidebar-url'))
        }
    }

    function flash_message_on_button(btn, kind = 'success') {
        let original_btn_html = btn.html();

        btn.text(btn.data(kind));
        btn.addClass(`btn-${kind}`);

        setTimeout(function () {
            btn.html(original_btn_html);
            btn.removeClass(`btn-${kind}`);
            if(btn.data('refresh-fragments') === 'yes') {
                refresh_fragments()
            }
        }, 1000);
    }

    // interactions / events
    body.on('click', '.modal-trigger', function (e) {
        let modalDialog = $('#character-modal .modal-dialog')
        $('.character-modal-container').load($(this).data('url'))
        $('.modal-header h5').text($(this).data('modal-title'))
        if ($(this).hasClass('small-modal')) {
            modalDialog.removeClass('modal-xl')
        } else {
            modalDialog.addClass('modal-xl')
        }
        $('#sidebar-right').css('width', '');
    })

    $('#character-modal').on('hidden.bs.modal', function (e) {
        refresh_fragments()
        $('.character-modal-container').html('')
    })

    body.on('click', '.sidebar-trigger', function (e) {
        let sidebar = $('#sidebar-right');
        $(sidebar).css('width', '330px');
        sidebar.find('h4:first').text($(this).data('sidebar-title'))
        sidebar.find('.sidebar-content')
            .data('sidebar-url', $(this).data('sidebar-url'))
            .load($(this).data('sidebar-url'))
    })

    body.on('click', '.sidebar-close', function () {
        $('#sidebar-right').css('width', '');
        return false;
    });

    body.on('click', '.action-link', function (e) {
        $.post($(this).attr('href'), function (data) {
            refresh_fragments()
        })
        if ($(this).hasClass('close-sidebar')) {
            $('#sidebar-right').css('width', '');
        }
        e.preventDefault()
        return false
    })

    body.on('submit', '.add-form', function (e) {
        let form = $(this)
        let btn = form.find('button')
        $.ajax(form.attr('action'),
            {
                type: 'POST',
                data: form.serialize(),
                success: function (data) {
                    if (data.status === 'ok') {
                        flash_message_on_button(btn)
                    } else {
                        flash_message_on_button(btn, 'danger')
                    }
                },
                error: function (data) {
                    flash_message_on_button(btn, 'danger')
                }
            });
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
    body.on('shown.bs.tab', 'a[data-bs-toggle="tab"]', function (e) {
        $($(e.target).attr('href')).find('.masonry-container').masonry({percentPosition: true})
    })
})
