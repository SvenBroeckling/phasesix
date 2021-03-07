let bsDefaults = {
        offset: false,
        width: '330px'
    },
    bsMain = $('.bs-offset-main')

function showSidebar() {

    let canvas = $('#bs-canvas-right'),
        opts = $.extend({}, bsDefaults, $(canvas).data()),
        prop = $(canvas).hasClass('bs-canvas-right') ? 'margin-right' : 'margin-left';

    if (opts.width === '100%')
        opts.offset = false;

    $(canvas).css('width', opts.width);
    if (opts.offset && bsMain.length)
        bsMain.css(prop, opts.width);

    return canvas
}

function hideSidebar() {
    $('.bs-canvas-close').click()
}

$('.bs-canvas-close').on('click', function () {
    let canvas, aria;
    if ($(this).hasClass('bs-canvas-close')) {
        canvas = $(this).closest('.bs-canvas');
        aria = $(this).add($('[data-toggle="canvas"][data-target="#' + canvas.attr('id') + '"]'));
        if (bsMain.length)
            bsMain.css(($(canvas).hasClass('bs-canvas-right') ? 'margin-right' : 'margin-left'), '');
    } else {
        canvas = $('.bs-canvas');
        aria = $('.bs-canvas-close, [data-toggle="canvas"]');
        if (bsMain.length)
            bsMain.css({
                'margin-left': '',
                'margin-right': ''
            });
    }
    canvas.css('width', '');
    return false;
});