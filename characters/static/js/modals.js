$(function () {
    let body = $('body')
    let pageModal = $('#page-modal')

    body.on('click', '.modal-trigger', function (e) {
        let modalDialog = $('#page-modal .modal-dialog')
        $('.modal-header h5').text($(this).data('modal-title'))
        pageModal.data('url', $(this).data('url'))
        if ($(this).hasClass('small-modal')) {
            modalDialog.removeClass('modal-xl')
        } else {
            modalDialog.addClass('modal-xl')
        }
        $('#sidebar-right').css('width', '');
    })

    pageModal.on('shown.bs.modal', function (e) {
        $('.page-modal-container').load(
            $(this).data('url'),
            function (response, status, xhr) {
                setTimeout(function () {
                    $(".page-modal-container .masonry-container").masonry({percentPosition: true})
                }, 200)
            }
        )
    })

    pageModal.on('hidden.bs.modal', function (e) {
        $('.page-modal-container').html('')
    })
})
