$(function() {
    $("meta[name=theme-color]").attr("content", "#cd071e");
    $("head").first().append("<script src='/static/themes/chinese_new_year/chinese_new_year-cookie.js'></script>");

    // Vary  flight path a little each load to make it look natural.
    const duration = 30 + Math.random() * 20;
    const delay = -Math.random() * duration;
    $("<img>")
        .addClass("cny-dragon")
        .attr("src", "/static/themes/chinese_new_year/dragon.png")
        .attr("alt", "")
        .css({
            "animation-duration": duration + "s",
            "animation-delay": delay + "s",
        })
        .appendTo("body");
});
