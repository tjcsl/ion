window.label_status_strings = {
    "a": {
        empty_text: "No buses have arrived yet.",
        name: "Arrived",
        personal: "has arrived.",
        icon: "check",
        color: "green",
    },
    "o": {
        empty_text: "All buses have arrived or are delayed.",
        name: "On Time",
        personal: "is on time.",
        icon: "clock",
        color: "blue",
    },
    "d": {
        empty_text: "No delays.",
        name: "Delayed",
        personal: "is delayed.",
        icon: "exclamation-triangle",
        color: "red",
    },
};

let now = new Date();
let end_time = new Date(now.getFullYear(), now.getMonth(), now.getDate(), parseInt(endHour), parseInt(endMinute), 0, 0);
let five_min_before_end = new Date(end_time.getFullYear(), end_time.getMonth(), end_time.getDate(), parseInt(endHour), parseInt(endMinute) - 5, 0, 0);

if(now.getTime() >= five_min_before_end.getTime()) {
    let o = window.label_status_strings.o;
    o.personal = "has not arrived yet.";
    o.icon = "exclamation-triangle";
    o.color = "orange";
}

// Turn off delayed alert for weekends
if(now.getDay() === 0 || now.getDay() === 6) {
    let o = window.label_status_strings.o;
    o.personal = "is on time.";
    o.icon = "clock";
    o.color = "blue";
}

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
    let userRouteName = null;

    socket.onopen = () => {
        if(keepAliveTimeoutId !== null) {
            clearTimeout(keepAliveTimeoutId);
            keepAliveTimeoutId = null;
        }

        if (disconnected_msg) {
            disconnected_msg.update({
                message: 'Connection established',
                type: 'success',
                hideAfter: 2
            });
        }
    };

    socket.onmessage = (event) => {
        if(keepAliveTimeoutId != null) {
            clearTimeout(keepAliveTimeoutId);
            keepAliveTimeoutId = null;
        }

        let data = JSON.parse(event.data);

        // Don't try and handle keepalives -- when handled, they effectively clear the bus board
        if(data.type === "keepalive-response") {
            return;
        }

        if(data.userRouteName) {
            userRouteName = processBusString(data.userRouteName);
        }

        if (document.getElementById('morning') !== null && document.getElementById('afternoon') !== null) {
            if (document.getElementById('morning').hidden === false) {
                time = 'morning';
            } else if (document.getElementById('afternoon').hidden === false) {
                time = 'afternoon';
            }
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
        if(data.announcement) {
            $(".bus-announcement-container").show();
            $(".bus-announcement").text(data.announcement);

            if(userRouteName && processBusString(data.announcement).includes(userRouteName)) {
                $(".bus-announcement-header").addClass("bus-announcement-alert");
                $(".bus-announcement-header i").addClass("fa-exclamation-circle");
                $(".bus-announcement").addClass("bus-announcement-alert");
            }
            else {
                $(".bus-announcement-header").removeClass("bus-announcement-alert");
                $(".bus-announcement-header i").removeClass("fa-exclamation-circle");
                $(".bus-announcement").removeClass("bus-announcement-alert");
            }

            if(isAdmin) {
                $(".bus-announcement-help").fadeOut(500);
            }
        }
        else {
            if(!isAdmin) {
                $(".bus-announcement-container").fadeOut(500);
            }
            else {
                $(".bus-announcement").text("");
                $(".bus-announcement-container").show();
                $(".bus-announcement-help").fadeIn(500);
            }
        }
    };

    socket.onclose = () => {
        if(window.Messenger) {
            disconnected_msg = Messenger().error({
                message: 'No connection',
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

function processBusString(name) {
    let patterns = [
        /\s+/g,
        "-",
        "jt",
        "ac",
        "lc",
        "pw",
    ]
    name = name.toLowerCase();
    patterns.forEach(pattern => {
        name = name.replaceAll(pattern, "");
    });
    return name;
}
