$(function() {
    let enabled = Cookies.get("disable-chinese-new-year") == "1" ? "0" : "1";

    $(".header > .right > ul").prepend(
        "<a class='toggle-cny-theme btn-link' onclick='toggleChineseNewYearTheme()'><i class='fas fa-dragon'></i>&nbsp;Turn "
        + (enabled == "1" ? "Off" : "On") + " Chinese New Year Theme</a>"
    );

    if (window.innerWidth < 1000) {
        $(".toggle-cny-theme").hide();
        $("ul.nav").append($(`
            <li>
                <a class='toggle-cny-theme' onclick='toggleChineseNewYearTheme()'>
                    <i class='fas fa-dragon' style="font-size: 16pt; position: relative; top: 3px; left: 6px;"></i>
                    <span style="position: relative; bottom: 9px; left: 15px;">
                        Turn` + (enabled == "1" ? " Off" : " On") + `
                        <br>
                        CNY Theme
                    </span>
                </a>
            </li>
        `));
    }
});

function toggleChineseNewYearTheme() {
    let enabled = Cookies.get("disable-chinese-new-year") == "1" ? "0" : "1";
    Cookies.set("disable-chinese-new-year", enabled, {expires: 7});
    location.reload();
}
