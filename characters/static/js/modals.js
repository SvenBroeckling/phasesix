$(function () {
    let body = $('body')

    body.on('click', '.modal-trigger', function (e) {
        let modalDialog = $('#page-modal .modal-dialog')
        $('.page-modal-container').load($(this).data('url'))
        $('.modal-header h5').text($(this).data('modal-title'))
        if ($(this).hasClass('small-modal')) {
            modalDialog.removeClass('modal-xl')
        } else {
            modalDialog.addClass('modal-xl')
        }
        $('#sidebar-right').css('width', '');
    })

    $('#page-modal').on('hidden.bs.modal', function (e) {
        refresh_fragments()
        $('.page-modal-container').html('')
    })
})
