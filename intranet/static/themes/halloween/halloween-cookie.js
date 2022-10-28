$(function() {
    $("head").first().append("<script nomodule src='/static/js/vendor/js.cookie.min.js'></script>");
    let enabled = Cookies.get("disable-halloween") == "1" ? "0" : "1";
    if(enabled == 1){
        $(".header > .right > ul").prepend(
            "<a style='color: white !important' class='toggle-halloween-theme btn-link' onclick='toggleHalloweenCookie()'><i class='fas fa-ghost'></i>  &nbsp;Turn Off Halloween Theme</a>"
        );
    }
    else {
        $(".header > .right > ul").prepend(
            "<a style='background: linear-gradient(to bottom, #08080B 0%, #0F0F0F 100%); color: orange !important' class='toggle-halloween-theme btn-link' onclick='toggleHalloweenCookie()'><i class='fas fa-ghost'></i>  &nbsp;Turn On Halloween Theme</a>"
        );
    }
});

function toggleHalloweenCookie() {
    let enabled = Cookies.get("disable-halloween") == "1" ? "0" : "1";
    Cookies.set("disable-halloween", enabled, {expires: 7});
    location.reload();
}
