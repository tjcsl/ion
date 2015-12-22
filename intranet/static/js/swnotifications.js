if(window.ion.authenticated && !window.ion.gcm_optout) {
    window.addEventListener('load', function() {
        if('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/serviceworker.js', { scope: './' }).then(subscribe);
        } else {
            console.warn('Service workers aren\'t supported in this browser.');
        }       
    });
}

function subscribe() {
    navigator.serviceWorker.ready.then(function(serviceWorkerRegistration) {
        serviceWorkerRegistration.pushManager.subscribe({ userVisibleOnly: true })
            .then(function(subscription) {
                
                return sendSubscriptionToServer(subscription);
            })
            .catch(function(e) {
                if (Notification.permission === 'denied') {
                    console.warn('Permission for Notification is denied');
                } else {
                    console.error('Unable to subscribe to push', e);
                }
            }
        );
    });
}



// send subscription id to server, to be saved linked to logged in user's UID
function sendSubscriptionToServer(subscription) {
    var res=subscription.endpoint.split("/")
    var token = res[res.length-1]
    console.log(token);
    if(window.ion && window.ion.authenticated) {
        var token_sha = sha256(token);
        if((!window.ion.gcm_token_sha || window.ion.gcm_token_sha != token_sha) && !window.ion.gcm_optout) {
            console.info("Updating GCM token...");
            $.post("/notifications/chrome/setup", {
                "token": token
            }, function(r) {
                console.debug(r);
            });
        } else {
            console.info("GCM token already saved.");
        }
    }

}