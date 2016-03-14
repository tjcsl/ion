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
    if($.cookie("no_notifications") == "true") {
        console.warn('User denied notification via cookie.');
        return;
    }
    navigator.serviceWorker.ready.then(function(serviceWorkerRegistration) {
        serviceWorkerRegistration.pushManager.subscribe({ userVisibleOnly: true })
            .then(function(subscription) {
                
                return sendSubscriptionToServer(subscription);
            })
            .catch(function(e) {
                if (Notification.permission === 'denied') {
                    console.warn('Permission for Notification is denied');
                    document.cookie = "no_notifications=true; expires=" + new Date(+new Date + 30 * 24 * 60 * 60 * 1000);
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
                // console.debug(r);
            });
        } else {
            console.info("GCM token already saved.");
        }
    }

}
