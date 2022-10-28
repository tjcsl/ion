$(function() {
    $("head").first().append("<script nomodule src='/static/js/vendor/js.cookie.min.js'></script>");
    $("head").first().append("<script nomodule src='/static/themes/halloween/halloween-cookie.js'></script>");
    $("<i>").addClass("ghost fas fa-ghost").appendTo($("body"));
    $("<i>").addClass("broom fas fa-broom").appendTo($("body"));
    $("<i>").addClass("hat-wizard fas fa-hat-wizard").appendTo($("body"));

    let background_images = ["default", "login", "bg1", "bg2", "bg3", "bg4", "bg5", "bg6"]
    let random_bg = background_images[Math.floor(Math.random() * background_images.length)];

    let seenDefaultBg = Cookies.get("seen-default-halloween-bg") == "1" ? "1" : "0";
    if (seenDefaultBg == "0") {
        Cookies.set("seen-default-halloween-bg", "1", {expires: 7});
        random_bg = "default";
    }
    if($("body").attr("class") == "login-page") {
        Cookies.set("seen-default-halloween-bg", "0", {expires: 7});
        random_bg = "login";
    }
    $("body").css("background-image", "url(/static/themes/halloween/bg/" + random_bg + ".jpg)");
});