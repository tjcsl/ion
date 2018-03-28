/* global $ */

var networkDataReceived = false;
var offline = false;

updatePage = function (data) {
    console.log('Writing new page');
    let parser = new DOMParser();
    let html = parser.parseFromString(data, 'text/html');
    $('body').empty();
    $('body').append($(html).find('body').children());
    console.log($(html));
};

networkUpdate = function () {
    fetch(window.location.pathname).then(function(response) {
        return response.text();
    }).then(function(data) {
        networkDataReceived = true;
        offline = false;
        updatePage(data);
    });
};

fetchFromCache = function () {
    caches.match(window.location.pathname).then(function(response) {
        if (!response) {
            throw Error('No data');
        }
        return response.text();
    }).then(function(data) {
        // don't overwrite newer network data
        if (!networkDataReceived) {
            updatePage(data);
        }
    }).catch(function() {
        // we didn't get cached data, the network is our last hope:
        return networkUpdate();
    }); //.catch(showErrorMessage).then(stopSpinner);
};

reloadPage = function () {
    networkUpdate();
    fetchFromCache();
};

window.addEventListener('online', function () {
    console.log('online!');
    reloadPage();
});

window.addEventListener('offline', function () {
    console.log('offline :(');
    offline = true;
});

window.onload = function () {
    window.setTimeout(function () {
        reloadPage();
    }, 20 * 60 * 1000);
};
