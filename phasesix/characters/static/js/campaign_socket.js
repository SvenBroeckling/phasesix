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
        if (data.type === 'tale_spire_roll_link') {
            console.log(data.message.url)
            window.location = data.message.url
            return
        }
        if (data.type === 'plot_item_reveal') {
            showPlayerReveal(data.message)
            return
        }
        if (data.type !== 'dice_roll') {
            return
        } else {
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
    }

    $('body').on('click', '.dice-roll', function (e) {
        let elem = $(this)
        let data = {
            type: 'dice_roll',
            roll: elem.data('dice-roll'),
            header: elem.data('dice-header'),
            description: elem.data('dice-description'),
            character: elem.data('dice-character'),
            campaign: elem.data('dice-campaign'),
            save_to: elem.data('dice-save-to')
        }
        socket.send(JSON.stringify(data))
    })

    $('body').on('click', '.show-to-players', function () {
        const elem = $(this)
        socket.send(JSON.stringify({
            type: elem.data('show-command'),
            campaign: elem.data('show-campaign'),
            item: elem.data('show-item')
        }))
    })

    function showPlayerReveal(reveal) {
        let modalElement = document.getElementById('player-reveal-modal')
        if (!modalElement) {
            modalElement = document.createElement('div')
            modalElement.id = 'player-reveal-modal'
            modalElement.className = 'modal fade'
            modalElement.tabIndex = -1
            modalElement.setAttribute('aria-label', reveal.name)
            modalElement.setAttribute('aria-hidden', 'true')
            modalElement.innerHTML = `
                <div class="modal-dialog modal-dialog-centered modal-lg">
                    <div class="modal-content atmospheric-modal border-0 bg-transparent">
                        <img class="img-fluid rounded" style="max-height: 85vh; object-fit: contain;" alt="">
                    </div>
                </div>`
            document.body.appendChild(modalElement)
        }

        const image = modalElement.querySelector('img')
        image.src = reveal.image_url
        image.alt = reveal.name
        bootstrap.Modal.getOrCreateInstance(modalElement).show()
    }
})
