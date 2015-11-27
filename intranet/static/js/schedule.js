$(document).ready(function() {

    scheduleBind = function() {
        $(".schedule-outer .schedule-left").click(function(event) {
            event.preventDefault();
            scheduleView(-1);
        });

        $(".schedule-outer .schedule-right").click(function(event) {
            event.preventDefault();
            scheduleView(1);
        });
    };

    genOrigSearch = function() {        
        var qs = location.search.substring(1);
        var osearch = "";
        var searchparts = qs.split("&");
        for (var i in searchparts) {
            // console.debug(searchparts[i]);
            if (searchparts[i].length > 0 && searchparts[i].substring(0, 5) !== "date=") {
                osearch += searchparts[i] + "&";
            }
        }
        return osearch;
    };

    window.osearch = genOrigSearch();
    // console.info("osearch:", window.osearch);

    scheduleView = function(reldate) {
        $sch = $(".schedule");
        var endpoint = $sch.attr("data-endpoint");
        var prev = $sch.attr("data-prev-date");
        var next = $sch.attr("data-next-date")
        if (reldate === 1) {
            date = next;
        } else if (reldate === -1) {
            date = prev;
        } else {
            date = reldate;
        }

        if (history.pushState) {
            var url = "?"+window.osearch+"date="+date;
            console.debug(url);
            history.pushState(null, null, url);
        }

        $.get(endpoint, {"date": date, "no_outer": true}, function(d) {
            $(".schedule-outer").html(d);
            scheduleBind();
            setTimeout(displayPeriod, 50);
        });
    };

    formatDate = function(date) {
        var parts = date.split("-");
        return new Date(parts[0], parts[1]-1, parts[2]);
    }

    formatTime = function(time, date) {
        var d = new Date(date);
        var tm = time.split(":");
        var hr = parseInt(tm[0]);
        var mn = parseInt(tm[1]);
        d.setHours(hr < 7 ? hr+12 : hr);
        d.setMinutes(mn)
        return d;
    }


    getPeriods = function() {
        $sch = $(".schedule");
        var blocks = $(".schedule-block[data-block-order]", $sch);
        var periods = [];
        var curDate = formatDate($sch.attr("data-date"));

        blocks.each(function() {
            var start = $(this).attr("data-block-start");
            var startDate = formatTime(start, curDate);

            var end = $(this).attr("data-block-end");
            var endDate = formatTime(end, curDate);

            periods.push({
                "name": $(this).attr("data-block-name"),
                "start": {
                    "str": start,
                    "date": startDate
                },
                "end": {
                    "str": end,
                    "date": endDate
                },
                "order": $(this).attr("data-block-order")
            });
        });

        return periods;
    }

    getPeriodElem = function(period) {
        return $(".schedule-block[data-block-order='" + period.order + "']");
    }

    withinPeriod = function(period, now) {
        var st = period["start"].date;
        var en = period["end"].date;
        return now >= st && now < en;
    }

    betweenPeriod = function(period1, period2, now) {
        var en = period1["end"].date;
        var st = period2["start"].date;
        return now >= en && now < st;
    }


    getCurrentPeriod = function(now) {
        $sch = $(".schedule");
        var curDate = formatDate($sch.attr("data-date"));
        var periods = getPeriods();
        if(!now) now = new Date();

        for(var i=0; i<periods.length; i++) {
            var period = periods[i];
            if(withinPeriod(period, now)) {
                return {
                    "status": "in",
                    "period": period
                };
            }
            if(i+1 < periods.length && betweenPeriod(period, periods[i+1], now)) {
                return {
                    "status": "between",
                    "prev": period,
                    "next": periods[i+1]
                };
            }
        }
        return false;
    }

    window.prevPeriod = null;
    displayPeriod = function(now) {
        $sch = $(".schedule");
        if(!now) var now = new Date();
        var current = getCurrentPeriod(now);
        // if(current != window.prevPeriod) console.debug(now.getHours()+":"+now.getMinutes(), "current:", current);
        window.prevPeriod = current;
        $(".schedule-block").removeClass("current");
        $(".schedule-block-between").remove()

        if(!current) {
            ;
        } else if(current["status"] == "in") {
            var p = getPeriodElem(current["period"]);
            p.addClass("current");
        } else if(current["status"] == "between") {
            var prev = getPeriodElem(current["prev"]);
            var next = getPeriodElem(current["next"]);
            var times = current["prev"]["end"].str + " - " + current["next"]["start"].str;
            prev.after("<tr class='schedule-block schedule-block-between current'><th>Passing:</th><td>" + times + "</td></tr>");
        }
    }

    scheduleBind(); 


    displayPeriod();
    setInterval(displayPeriod, 10000);
});
