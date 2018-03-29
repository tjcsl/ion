/* global $ */

var networkDataReceived = false;
var offline = false;
var active = null;

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

var setActive = function (id) {
    $('.active').removeClass('active');
    page = document.getElementById(id);
    $(page).addClass('active');
    active = id;
};

window.addEventListener('online', function () {
    console.log('online!');
    reloadPage();
    if (active) {
        console.log('setting active');
        setActive(active);
    }
});

window.addEventListener('offline', function () {
    console.log('offline :(');
    offline = true;
});

window.onload = function () {
    window.setTimeout(function () {
        reloadPage();
    }, 20 * 60 * 1000);

    setInterval(function() {
        var now = new Date();
        var hr = now.getHours();
        var ampm = 'AM';
        if (hr === 0) {
            hr = 12;
        }
        if (hr > 12) {
            hr -= 12;
            ampm = 'PM';
        }
        var min = now.getMinutes();
        if (min < 10) {
            min = '0' + min;
        }
        $('.time').html(hr + ':' + min + ' ' + ampm);
    }, 1000);
};
