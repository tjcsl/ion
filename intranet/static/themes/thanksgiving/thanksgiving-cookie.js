
$(function () {
    $('.header > .right > ul').prepend(
        '<a onclick="toggleThanksgivingCookie()" style="color:#ffffff !important;cursor:pointer;text-decoration:none;margin-right:10px;font-family:inherit;font-size:inherit;">&#127810; Turn On Thanksgiving Theme</a>'
    );

    if (window.innerWidth < 1000) {
        var li = document.createElement('li');
        li.innerHTML = '<a onclick="toggleThanksgivingCookie()" style="color:inherit !important;cursor:pointer;">' +
            '<i class="fas fa-leaf" style="font-size:16pt;position:relative;top:3px;left:6px;"></i>' +
            '<span style="position:relative;bottom:9px;left:15px;">Turn On<br>Thanksgiving Theme</span>' +
            '</a>';
        document.querySelector('ul.nav').appendChild(li);
    }
});

function toggleThanksgivingCookie() {
    var enabled = Cookies.get('disable-thanksgiving') == '1' ? '0' : '1';
    Cookies.set('disable-thanksgiving', enabled, { expires: 7 });
    location.reload();
}