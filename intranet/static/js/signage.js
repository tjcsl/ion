/* global $ */

/* Some notes:
 *      - I hacked together a routing thing and never ended up using backbone
 * */

var networkDataReceived = false;
var offline = false; // This isn't used for anything useful
var active = null;

var setActive = function (id) {
    $('.active').removeClass('active');
    page = document.getElementById(id);
    if (page) {
        $(page).addClass('active');
        $('.signage-nav').addClass('show-back');
        active = id;
        window.location.hash = `#page-${id}`;
    } else {
        $('.signage-nav').removeClass('show-back');
        active = 'home';
        window.location.hash = '#page-home';
    }
};

var resetPage = function () {
    console.log('Resetting Page');
    if (window.location.hash) {
        pageid = window.location.hash.split('-')[1];
        setActive(pageid);
    }
};

updatePage = function (data) {
    console.log('Writing new page');
    let parser = new DOMParser();
    let html = parser.parseFromString(data, 'text/html');
    $('body').empty();
    $('body').append($(html).find('body').children());

    resetPage();

    if (!navigator.onLine) {
        console.log('offline :(');
        $('.message').addClass('offline');
        offline = true;
    }
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
    if (active) {
        console.log('setting active');
        setActive(active);
    }
});

window.addEventListener('offline', function () {
    console.log('offline :(');
    $('.message').addClass('offline');
    offline = true;
});

window.onload = function () {
    $('.signage-nav').on('click', 'a', function (e) {
        page = $(e.target).data('page');
        console.log(e);
        console.log(page);
        setActive(page);
    });

    window.setTimeout(function () {
        reloadPage();
    }, 20 * 60 * 1000);

    resetPage();

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
