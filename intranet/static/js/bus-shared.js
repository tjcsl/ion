export function getSocket(base_url, location, document, window, time) {
    const protocol = (location.protocol.indexOf('s') > -1) ? 'wss' : 'ws';
    let socket;
    if (base_url !== '') {
        socket = new ReconnectingWebSocket(`${protocol}://${base_url}/bus/`);
    } else {
        socket = new ReconnectingWebSocket(`${websocketProtocol}://${websocketHost}/bus/`);
    }
    socket.automaticOpen = true;
    socket.reconnectInterval = 2000;
    socket.maxReconnectInterval = 10000;
    socket.reconnectDecay = 1.25;
    socket.timeoutInterval = 5000;
    socket.maxReconnectAttempts = null;

    let disconnected = false;
    let disconnected_msg = null;
    let keepAliveTimeoutId = null;

    socket.onopen = () => {
        if(keepAliveTimeoutId !== null) {
            clearTimeout(keepAliveTimeoutId);
            keepAliveTimeoutId = null;
        }

        if (disconnected_msg) {
            disconnected_msg.update({
                message: 'Connection Restored',
                type: 'success',
                hideAfter: 3
            });
        }
    };

    socket.onmessage = (event) => {
        if(keepAliveTimeoutId != null) {
            clearTimeout(keepAliveTimeoutId);
            keepAliveTimeoutId = null;
        }

        var data = JSON.parse(event.data)

        // Don't try and handle keepalives -- when handled, they effectively clear the bus board
        if(data.type === "keepalive-response") {
            return;
        }

        if (document.getElementById('morning').hidden === false) {
            time = 'morning';
        } else if (document.getElementById('afternoon').hidden === false) {
            time = 'afternoon';
        }

        if (time === 'afternoon') {
            window.appView.trigger('wss:receive', data);
        } else if (time === 'morning') {
            var arrived = document.getElementById('arrived');
            var ontime = document.getElementById('ontime');
            var delayed = document.getElementById('delayed');
            arrived.innerHTML = "";
            ontime.innerHTML = "";
            delayed.innerHTML = "";
            for (let i = 0; i < data.allRoutes.length; i++) {
                let val = data.allRoutes[i];
                let new_p = document.createElement('p');
                new_p.innerHTML = data.allRoutes[i].route_name;
                if (val.status == 'a') {
                    arrived.appendChild(new_p);
                } else if (val.status == 'o') {
                    ontime.appendChild(new_p);
                } else {
                    delayed.appendChild(new_p);
                }
            }
        }
    };

    socket.onclose = () => {
        console.log('Disconnected');
        if(window.Messenger) {
            disconnected_msg = Messenger().error({
                message: 'Connection Lost',
                hideAfter: 0,
                showCloseButton: false
            });
        }
        disconnected = true;

        if(keepAliveTimeoutId != null) {
            clearTimeout(keepAliveTimeoutId);
            keepAliveTimeoutId = null;
        }
    };

    setInterval(function() {
        if(!disconnected) {
            socket.send(JSON.stringify({"type": "keepalive"}));

            keepAliveTimeoutId = setTimeout(function() {
                if(!disconnected) {
                    socket.refresh();
                }
            }, 10000);
        }
    }, 30000);

    return socket;
}
