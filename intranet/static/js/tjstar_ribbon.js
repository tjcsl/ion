$(function() {
    $("head").first().append("<script nomodule src='/static/js/vendor/js.cookie.min.js'><\/script>");
    let collapse_tjstar_ribbon = Cookies.get("collapse_tjstar_ribbon") == "1" ? true : false;
    if(!collapse_tjstar_ribbon) {
        $(".tjstar-ribbon-content").fadeIn("slow");
        $(".tjstar-ribbon-toggle").hide();
    }

    // Countdown timer initialization
    let countdownEl = $(".tjstar-countdown");
    let daysEl = $(".tjstar-countdown-days");
    let hoursEl = $(".tjstar-countdown-hours");
    let minutesEl = $(".tjstar-countdown-minutes");
    let secondsEl = $(".tjstar-countdown-seconds");

    let now = new Date();
    let distance = tjStarDate - now;
    let days = Math.floor(distance / (1000 * 60 * 60 * 24));
    let hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    let minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    let seconds = Math.floor((distance % (1000 * 60)) / 1000);

    if(days <= 0 && hours <= 8) {
        $(".tjstar-ribbon-toggle-text").text("Today!").css("color", "#0fa674").css("font-weight", "bold");
        // Auto expand the ribbon on tjSTAR day
        if(!(hours < -4 || (hours == -4 && minutes <= -20))) {
            Cookies.set("collapse_tjstar_ribbon", "0", { expires: 21 })
            $(".tjstar-ribbon-content").slideDown();
            $(".tjstar-ribbon-toggle").slideUp();
            $(".tjstar-ribbon-collapse").hide();
        }
    }

    // Countdown timer
    let tjStarTimer = setInterval(function() {
        now = new Date();
        distance = tjStarDate - now;
        days = Math.floor(distance / (1000 * 60 * 60 * 24));
        hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        seconds = Math.floor((distance % (1000 * 60)) / 1000);

        //console.log(days, hours, minutes, seconds)

        if (distance <= 0) {
            clearInterval(tjStarTimer);
            countdownEl.text("tjSTAR has started!");
            if(hours <= -1 && minutes <= -10) {
                countdownEl.text("tjSTAR is ongoing!");
            }
            if(hours < -4 || (hours == -4 && minutes <= -20)) {
                countdownEl.text("tjSTAR has ended!").css("color", "#F25B54");
            }
            countdownEl.fadeTo(500, 1);
            return;
        }

        daysEl.text(days + "d ");
        hoursEl.text(hours + "h ");
        minutesEl.text(minutes + "m ");
        secondsEl.text(seconds + "s ");

        $(".tjstar-countdown").fadeTo(500, 1);
    }, 1000);

    $(".tjstar-ribbon-collapse").click(function() {
        $(".tjstar-ribbon-content").slideUp();
        $(".tjstar-ribbon-toggle").slideDown();
        Cookies.set("collapse_tjstar_ribbon", "1", { expires: 21 });
    });

    $(".tjstar-ribbon-toggle").click(function() {
        $(".tjstar-ribbon-content").slideDown();
        $(".tjstar-ribbon-toggle").slideUp();
        Cookies.set("collapse_tjstar_ribbon", "0", { expires: 21 });
    });
});