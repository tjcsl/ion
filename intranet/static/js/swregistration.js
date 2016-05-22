window.addEventListener('load', function() {
    var outputElement = document.getElementById('output');
    navigator.serviceWorker.register('/serviceworker.js', { scope: './' })
             .then(function(r) {
                 console.log('registered service worker');
             }).catch(function(whut) {
                 console.error('service worker failed to register');
                 console.error(whut);
             });

    window.addEventListener('beforeinstallprompt', function(e) {
        /* */
    });
});