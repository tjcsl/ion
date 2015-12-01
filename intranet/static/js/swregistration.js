window.addEventListener('load', function() {
  var outputElement = document.getElementById('output');
  navigator.serviceWorker.register('/static/js/service-worker.js', { scope: './' })//correct scope?
    .then(function(r) {
      console.log('registered service worker');
    })
    .catch(function(whut) {
      console.error('uh oh... ');
      console.error(whut);
    });
   
  window.addEventListener('beforeinstallprompt', function(e) {
    
  });
});