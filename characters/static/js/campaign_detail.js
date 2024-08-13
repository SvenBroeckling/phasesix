$('.campaign-link').on('click', function (e) {
    let elem = $(this)
    let text = $(this).find(".invite-text")
    let orig_text = text.text()
    copyTextToClipboard(elem.attr('href'))

    text.text(elem.data('msg'))
    setTimeout(() => text.text(orig_text), 2000)

    e.preventDefault()
    return false
})

$('table.campaign-status-sortable').tablesorter({
    textExtraction: {
        '.data': function (node, table, cellIndex) {
            return $(node).find('span.sort-key').text()
        }
    }
})

let body = $('body')
body.on('click', 'a[data-bs-toggle="tab"]', function (e) {
    let target = $(e.target).closest('a[data-bs-toggle="tab"]').attr('data-bs-target')
    if (target) {
        $(target).find('.masonry-container').masonry({percentPosition: true})
    }
})
