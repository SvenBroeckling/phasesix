$(function(){
    const room_name = $('#room-name').text()
    let socket = new WebSocket(`wss://${window.location.host}/ws/campaign/${room_name}/`)

    socket.onerror = (e) => {
        console.error(`Connection error: ${e}`)
    }

    socket.onmessage = (e) => {
        const data = JSON.parse(e.data)
        const displayResults = $('#display-ws-dice-results').prop('checked')

        if(displayResults){
            Toast.setPlacement(TOAST_PLACEMENT.BOTTOM_LEFT)
            Toast.setMaxCount(7)
            Toast.create({
                title: data.message.character,
                message: `${data.message.header} <small class="text-muted">${data.message.description}</small><br>${data.message.result_html}`,
                status: TOAST_STATUS.SUCCESS
            })
        }
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