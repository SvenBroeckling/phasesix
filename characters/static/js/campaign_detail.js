$('.campaign-link').on('click', function (e) {
    let elem = $(this)
    let orig_text = elem.text()
    copyTextToClipboard(elem.attr('href'))

    elem.text(elem.data('msg'))
    setTimeout(() => elem.text(orig_text), 1000)

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
