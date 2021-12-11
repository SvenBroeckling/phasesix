$(function(){
    const room_name = $('#room-name').text()
    let socket = new WebSocket(`ws://${window.location.host}/ws/campaign/${room_name}/`)

    const t = JSON.stringify({'message': 'hello'})
    setTimeout(() => {socket.send(t)}, 4000)

    socket.onerror = (e) => {
        console.error(`Connection error: ${e}`)
    }

    socket.onmessage = (e) => {
        const data = JSON.parse(e.data)
        console.log(`Message: ${data.message}`)
    }
})