$(function () {
    let body = $('body')
    body.on('click', '.sidebar-trigger', function (e) {
        let sidebar = $('#sidebar-right');
        $(sidebar).css('width', '330px');
        sidebar.find('h4:first').text($(this).data('sidebar-title'))
        if ($(this).hasClass('sidebar-spinner')) {
            sidebar.find('.sidebar-content').html('<div class="w-100 pt-5 d-flex justify-content-center align-content-center"><i class="fas fa-spinner fa-3x fa-spin"></i></div>')
        }
        sidebar.find('.sidebar-content')
            .data('sidebar-url', $(this).data('sidebar-url'))
            .load($(this).data('sidebar-url'))
        e.preventDefault();
        return false;
    })

    body.on('click', '.sidebar-close', function () {
        $('#sidebar-right').css('width', '');
        return false;
    });
})
