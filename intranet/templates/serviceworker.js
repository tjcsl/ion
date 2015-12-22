var self = this;

self.addEventListener('push', function(event) {
    console.log('Received a push message', event);

    var data = {};
    if(event.data) {
        data = event.data.json();
        console.debug(data);
        showNotif(event, data)
    } else {
        var evt = event;
        console.debug("Fetching data text...")
        fetch("/notifications/chrome/getdata", { credentials: 'include' }).then(function(r) {
            console.debug(r);
            var j = r.json();
            console.debug(j);
            showNotif(evt, j);
        });
    }
    
    
    showNotif = function(event, data) {
        //replace with message data fetched from Ion API/DB based on logged in user's UID
        var title = data.title || "[Unable to fetch title]";
        var body = data.text || "Click here for more information."
        var icon = '/static/img/logos/touch/touch-icon128.png';
        var tag = data.tag || 'ion-notification';

        self.registration.showNotification(title, {
            body: body,
            icon: icon,
            tag: tag
        });
    }

});

self.addEventListener('notificationclick', function (event) {
    var tag = event.notification.tag;
    console.log('Notification click: ', tag);

    event.notification.close();

    var tagUrl = '/';
    var tags = tag.split("=");
    if(tags[0] == "url") {
        tagUrl = "/"+tags[1];
    }

    event.waitUntil(
        clients.matchAll({
            type: 'window'
        })
            .then(function(clientList){
                for (var i = 0; i < clientList.length; i++) {
                    var client = clientList[i];
                    if (client.url === tagUrl && 'focus' in client) {
                        return client.focus();
                    }
                }
                if (clients.openWindow) {
                    return clients.openWindow(tagUrl);
                }
            })
    );
})
