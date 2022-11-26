$(function () {
    let body = $('body')

    // helper
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

    body.on('click', '.submit-button', function (e) {
        let form = $(this).closest('form')
        let url = form.attr('action')
        let form_data = form.serialize()

        $.post(url, form_data, function (data) {
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

})
