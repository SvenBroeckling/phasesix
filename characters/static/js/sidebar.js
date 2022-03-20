$(function() {
    let body = $('body')
    body.on('click', '.sidebar-trigger', function (e) {
        let sidebar = $('#sidebar-right');
        $(sidebar).css('width', '330px');
        sidebar.find('h4:first').text($(this).data('sidebar-title'))
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