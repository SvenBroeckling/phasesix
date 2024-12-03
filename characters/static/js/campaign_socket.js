$(function () {
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

        let diceLogVisible = document.querySelector("#dice-log.show")

        if (!diceLogVisible) {
            Toast.setPlacement(TOAST_PLACEMENT.BOTTOM_LEFT)
            Toast.setMaxCount(5)
            Toast.create({
                title: data.message.character,
                message: `${data.message.header} <small class="text-muted">${data.message.description}</small><br>${data.message.result_html}`,
                status: TOAST_STATUS.SUCCESS,
                timeout: 5000,
            })
        }

        let diceLogEntries = document.querySelector("#dice-log-entries")
        if (diceLogEntries) {
            let html = `${data.message.character} - ${data.message.header} ${data.message.result_html}<hr>`
            diceLogEntries.innerHTML = html + diceLogEntries.innerHTML;
            diceLogEntries.scrollTop = 0
        }

        audioElement.play()
    }

    $('body').on('click', '.dice-roll', function (e) {
        let elem = $(this)
        let data = {
            roll: elem.data('dice-roll'),
            header: elem.data('dice-header'),
            description: elem.data('dice-description'),
            character: elem.data('dice-character'),
            campaign: elem.data('dice-campaign'),
            save_to: elem.data('dice-save-to')
        }
        socket.send(JSON.stringify(data))
    })
})

function toggleDiceLog() {
    const diceLog = document.getElementById('dice-log');
    if (diceLog) diceLog.classList.toggle('show');
}

