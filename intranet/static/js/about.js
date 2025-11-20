/* global $ */
$(function() {
    $(".logo").click(function() {
        location.href = '/';
    });

    var desktop = $(".desktop-area"),
        mobile = $(".mobile-area");
    var desktopMax = $("span", desktop).length,
        mobileMax = $("span", mobile).length;
    var desktopIndex = 0,
        mobileIndex = 0;
    setInterval(function() {
        if (desktopIndex === desktopMax - 1) {
            $("span", desktop).eq(0).slideDown();
            $("span", desktop).show();
            desktopIndex = 0;
        } else {
            $("span", desktop).eq(desktopIndex).slideUp();
            desktopIndex++;
        }

        if (mobileIndex === mobileMax - 1) {
            $("span", mobile).eq(0).slideDown();
            setTimeout(function() {
                $("span", mobile).show();
            }, 500);
            mobileIndex = 0;
        } else {
            $("span", mobile).eq(mobileIndex).slideUp();
            mobileIndex++;
        }
    }, 5000);
});