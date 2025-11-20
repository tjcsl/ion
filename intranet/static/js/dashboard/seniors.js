/* global $ */
function getTimeRemaining(endtime) {
    var t = Date.parse(endtime) - Date.parse(new Date());
    var seconds = Math.floor((t / 1000) % 60),
        minutes = Math.floor((t / 1000 / 60) % 60),
        hours = Math.floor((t / (1000 * 60 * 60)) % 24),
        days = Math.floor(t / (1000 * 60 * 60 * 24));
    return {
        'total': t,
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds
    };
}

function initClock(id, evt, endtime) {
    var clock = document.querySelector(id);
    if (!clock) return;

    function updateClock() {
        var t = getTimeRemaining(endtime);

        var dys = t.days,
            hrs = t.hours,
            mns = t.minutes,
            scs = ('0' + t.seconds).slice(-2);

        if (dys > 50) {
            clock.innerHTML = "<span class='clock'><b>" + dys + "</b> days, <b>" + hrs + "</b> hours</span> until " + evt;
        } else {
            clock.innerHTML = "<span class='clock'><b>" + dys + "</b> days, <b>" + hrs + "</b> hours, <b>" + mns + "</b> minutes, <b>" + scs + "</b> seconds</span><br>until " + evt;
        }

        if (t.total <= 0) {
          clearInterval(timeinterval);
          clock.innerHTML = "<span class='clock'><b style='font-weight:bold'>YOU HAVE GRADUATED!</b></span>";
          if (typeof graduated !== "undefined") graduated();
        }
    }
    updateClock();
    var timeinterval = setInterval(updateClock, 500);
}

$(function() {
    var graddate = $(".seniors-widget").attr("data-graduation-date");
    var deadline = graddate + " GMT-0400 (EDT)";
    initClock(".seniors-clock", "Graduation!", deadline);
});
