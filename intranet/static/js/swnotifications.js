  window.addEventListener('load', function() {
       
        
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/serviceworker.js', { scope: './' })
                .then(subscribe);
        } else {
            console.warn('Service workers aren\'t supported in this browser.');
        }
        
    });
    


 


    
    function subscribe() {
       

        navigator.serviceWorker.ready.then(function(serviceWorkerRegistration) {
            serviceWorkerRegistration.pushManager.subscribe({ userVisibleOnly: true })
                .then(function(subscription) {
                    

                   

                    return sendSubscriptionToServer(subscription);
                })
                .catch(function(e) {
                    if (Notification.permission === 'denied') {
                        console.warn('Permission for Notification is denied');
                        pushButton.disabled = true;
                    } else {
                        console.error('Unable to subscribe to push', e);
                        pushButton.disabled = true;
                        pushButton.textContent = 'Enable Push Messages';
                    }
                })
        })
    }
    
   

    // send subscription id to server, to be saved linked to logged in user's UID
    function sendSubscriptionToServer(subscription) {
        

        var res=subscription.endpoint.split("/")
        var end=res[res.length-1]
        console.log(end)


    }