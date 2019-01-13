/* global $ */
$(function() {
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

    genOrigSearch = function(part_exclude) {
        var qs = location.search.substring(1);
        var osearch = "";
        var searchparts = qs.split("&");
        for (var i in searchparts) {
            // console.debug(searchparts[i]);
            if (searchparts[i].length > 0 && searchparts[i].substring(0, part_exclude.length + 1) !== (part_exclude + "=")) {
                osearch += searchparts[i] + "&";
            }
        }
        return osearch;
    };

    window.osearch = genOrigSearch("date");
    // console.info("osearch:", window.osearch);

    scheduleView = function(reldate) {
        $sch = $(".schedule");

        var endpoint = $sch.attr("data-endpoint");
        var prev = $sch.attr("data-prev-date");
        var next = $sch.attr("data-next-date");

        if (reldate === 1) date = next;
        else if (reldate === -1) date = prev;
        else date = reldate;

        if (history.pushState) {
            var nosearch = genOrigSearch("date");
            if (nosearch !== window.osearch) {
                window.osearch = nosearch;
            }
            var url = "?" + window.osearch + "date=" + date;
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
        // console.log("date: " + date);
        var parts = date.split("-");
        return new Date(parts[0], parts[1] - 1, parts[2]);
    }

    formatTime = function(time, date) {
        var d = new Date(date);
        var tm = time.split(":");
        var hr = parseInt(tm[0], 10);
        var mn = parseInt(tm[1], 10);
        d.setHours(hr < 7 ? hr + 12 : hr);
        d.setMinutes(mn)
        return d;
    }

    getPeriods = function() {
        $sch = $(".schedule");
        var blocks = $(".schedule-block[data-block-order]", $sch);
        var curDate = formatDate($sch.attr("data-date"));

        return blocks.map(function() {
            var date = curDate;
            var tbl = $(this).closest("table.bellschedule-table");
            if(tbl.attr("data-date") != null) {
                date = formatDate(tbl.attr("data-date"));
            }

            var start = $(this).attr("data-block-start");
            var startDate = formatTime(start, date);

            var end = $(this).attr("data-block-end");
            var endDate = formatTime(end, date);

            return {
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
            };
        });
    }

    getPeriodElem = function(period) {
        var elems = $(".schedule-block[data-block-order='" + period.order + "']");
        if(elems.length > 1) {
            //We're probably on the calendar view; try and find today's block specifically
            for(var i = 0; i < elems.length; i++) {
                var elem = $(elems.get(i));
                if(elem.closest("table.bellschedule-table").closest("td").hasClass("today")) {
                    return elem;
                }
            }
        }
        return elems;
    }

    withinPeriod = function(period, now) {
        var st = period.start.date;
        var en = period.end.date;
        return now >= st && now < en;
    }

    betweenPeriod = function(period1, period2, now) {
        var en = period1.end.date;
        var st = period2.start.date;
        return now >= en && now < st;
    }

    getCurrentPeriod = function(now) {
        $sch = $(".schedule");
        var schDate = $sch.attr("data-date");
        if (!schDate) return;
        var curDate = formatDate(schDate);
        var periods = getPeriods();
        if (!now) now = new Date();

        for (var i = 0; i < periods.length; i++) {
            var period = periods[i];
            if (withinPeriod(period, now)) {
                return {
                    "status": "in",
                    "period": period
                };
            } else if (i + 1 < periods.length && betweenPeriod(period, periods[i + 1], now)
                       && period.end.date.toDateString() == periods[i + 1].start.date.toDateString()) {
                return {
                    "status": "between",
                    "prev": period,
                    "next": periods[i + 1]
                };
            }
        }

        return false;
    }

    window.prevPeriod = null;
    displayPeriod = function(now) {
        $sch = $(".schedule");
        if (!now) now = new Date();
        var current = getCurrentPeriod(now);
        // if (current !== window.prevPeriod) console.debug(now.getHours() + ":" + now.getMinutes(), "current:", current);
        window.prevPeriod = current;
        $(".schedule-block").removeClass("current");
        $(".schedule-block-between").remove()

        // If the date has changed -- the <td> with the 'today' class is not actually today -- update the classes
        var today_td = $sch.find("td.today");
        var dateString = new Date().toISOString().slice(0, 10);;
        if(today_td.find("table.bellschedule-table").attr("data-date") != dateString) {
            today_td.removeClass("today");
            $("table.bellschedule-table[data-date='" + dateString + "']").closest("td").addClass("today");
        }

        if (current) {
            if (current.status === "in") {
                var p = getPeriodElem(current.period);
                p.addClass("current");
            } else if (current.status === "between") {
                var prev = getPeriodElem(current.prev),
                    next = getPeriodElem(current.next);
                var times = current.prev.end.str + " - " + current.next.start.str;
                prev.after("<tr class='schedule-block schedule-block-between current'><th>Passing:</th><td>" + times + "</td></tr>");
            }
        }
    }

    scheduleBind();

    displayPeriod();
    setInterval(displayPeriod, 10000);
});
