$(function(){
    let socket = new ReconnectingWebSocket($('#room-url').text(), null, {reconnectInterval: 3000})
    let indicator = $('#dice-ws-connected')

    socket.onopen = (e) => {
        indicator.removeClass('text-warning')
            .addClass('text-primary')
            .attr('title', indicator.data('message-connected'))
    }
    socket.onerror = (e) => {
        indicator.removeClass('text-primary')
            .addClass('text-warning')
            .attr('title', indicator.data('message-disconnected'))
    }

    socket.onclose = (e) => {
        indicator.removeClass('text-primary')
            .addClass('text-warning')
            .attr('title', indicator.data('message-disconnected'))
    }

    socket.onmessage = (e) => {
        const data = JSON.parse(e.data)
        const audioElement = document.getElementById('room-audio')

        Toast.setPlacement(TOAST_PLACEMENT.BOTTOM_LEFT)
        Toast.setMaxCount(7)
        Toast.create({
            title: data.message.character,
            message: `${data.message.header} <small class="text-muted">${data.message.description}</small><br>${data.message.result_html}`,
            status: TOAST_STATUS.SUCCESS,
            timeout: 10000,
        })
        audioElement.play()
    }

    $('body').on('click', '.dice-roll', function(e) {
        let elem = $(this)
        let data = {
            roll: elem.data('dice-roll'),
            header: elem.data('dice-header'),
            description: elem.data('dice-description'),
            character: elem.data('dice-character')
        }
        socket.send(JSON.stringify(data))
    })
})