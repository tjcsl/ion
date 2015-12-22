var self = this;
self.addEventListener('push', function(event) {
    console.log('Received a push message', event);
    

    //replace with message data fetched from Ion API/DB based on logged in user's UID
    var title = 'New title.';
    var body = 'We have received a push message.';
    var icon = '';//url to icon
    var tag = 'simple-push-demo-notification-tag';

    
    event.waitUntil(
        self.registration.showNotification(title, {
            body: body,
            icon: icon,
            tag: tag
        })
    );
    console.log("Icon:")
    console.log(icon)
});

self.addEventListener('notificationclick', function (event) {
    console.log('On notification click: ', event.notification.tag);

    event.notification.close();

    event.waitUntil(
        clients.matchAll({
            type: 'window'
        })
            .then(function(clientList){
                for (var i = 0; i < clientList.length; i++) {
                    var client = clientList[i];
                    if (client.url === '/' && 'focus' in client) {
                        return client.focus();
                    }
                }
                if (clients.openWindow) {
                    return clients.openWindow('/');
                }
            })
    );
})
