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
    if (window.innerWidth < 1000) {
        $(".toggle-halloween-theme").hide();
        let navbar = $("ul.nav");

        $(navbar).append($(`
            <li>
                <a class='toggle-halloween-theme' onclick='toggleHalloweenCookie()'>
                    <i class='fas fa-ghost' style="font-size: 16pt; position: relative; top: 3px; left: 6px;"></i>
                    <span class="halloween-nav-text" style="position: relative; bottom: 9px; left: 15px;">
                        Turn` + (enabled == 1 ? " Off" : " On") + `
                        <br>
                        Halloween Theme
                    </span>
                </a>
            </li>
        `));
    }
});

function toggleHalloweenCookie() {
    let enabled = Cookies.get("disable-halloween") == "1" ? "0" : "1";
    Cookies.set("disable-halloween", enabled, {expires: 7});
    location.reload();
}
