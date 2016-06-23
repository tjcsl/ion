/* global $ */
$(function() {
    searchDebug = false;

    function eighthSearch(q) {
        var _st = +new Date();

        var searchStr = $(this).val().toLowerCase();
        searchStr = $.trim(searchStr);

        var searchSplit = [];
        if (searchStr.indexOf('"') !== -1) {
            var quoteSplit = searchStr.split('"');
            for (var i = 0; i < quoteSplit.length; i++) {
                if (i === 0 || i === quoteSplit.length - 1) {
                    // first and last entries aren't inside the quote
                    var innerSplit = quoteSplit[i].split(" ");
                    for (var j = 0; j < innerSplit.length; j++) {
                        var inw = innerSplit[j];
                        if (inw.length > 0) searchSplit.push($.trim(inw));
                    }
                } else {
                    searchSplit.push($.trim(quoteSplit[i]));
                }
            }
        } else {
            var spaceSplit = searchStr.split(" ");
            for (var i = 0; i < spaceSplit.length; i++) {
                var spl = spaceSplit[i];
                if (spl.length > 0) searchSplit.push($.trim(spl));
            }
        }

        if (searchStr.length === 0) {
            $("#activity-picker").removeClass("has-search-header");
        } else {
            $("#activity-picker").addClass("has-search-header");
            $(".clear-button").click(function() {
                $("#activity-picker .search-wrapper input").val("").keyup();
            });
        }

        // console.log("query:", searchStr);

        var results = [];
        var activities = window.activityModels._byId;

        var showAdminact = false;

        $("#activity-list li[data-activity-id]").each(function() {
            var aid = $(this).data("activity-id");
            var activity = activities[aid].attributes;

            var shows = [];
            var queries = [];

            var show = false;

            for (var sp in searchSplit) {
                var search = searchSplit[sp];

                // blank entry
                if (search.length < 1 || search === '*') {
                    show = true;
                    results.push(aid);
                    continue; // skip
                }

                // - = inverse
                var inv = false;
                if (search.substring(0, 1) === "-") {
                    //console.log("INVERSE");
                    search = search.substring(1);
                    inv = true;
                }

                show = false;

                // aids
                if (parseInt(search) === parseInt(aid)) {
                    show = true;
                }
                // name + comments
                if (activity.name_with_flags_for_user.toLowerCase().indexOf(search) !== -1) {
                    show = true;
                }
                // sponsors
                for (var sp in activity.sponsors) {
                    if (activity.sponsors[sp].toLowerCase().indexOf(search) !== -1) {
                        show = true;
                    }
                }
                // rooms
                for (var rm in activity.rooms) {
                    if (activity.rooms[rm].toLowerCase().indexOf(search) !== -1) {
                        show = true;
                    }
                }

                var cmd = search.split(":");
                if (cmd.length > 1) {
                    // not: = inverse
                    var fl = !(cmd[0] === "not" || (cmd[0] === "is" && inv));
                    // restricted
                    if (cmd[1].substring(0, 1) === "r" && activity.restricted === fl) {
                        show = true;
                    }
                    // authorized
                    if (cmd[1].substring(0, 2) === "au" && activity.restricted === fl && activity.restricted_for_user === !fl) {
                        show = true;
                    }
                    // cancelled
                    if (cmd[1].substring(0, 1) === "c" && activity.cancelled === fl) {
                        show = true;
                    }
                    // bothblocks
                    if (cmd[1].substring(0, 1) === "b" && activity.both_blocks === fl) {
                        show = true;
                    }
                    // oneaday
                    if (cmd[1].substring(0, 2) === "on" && activity.one_a_day === fl) {
                        show = true;
                    }
                    // favorite
                    if (cmd[1].substring(0, 1) === "f" && activity.favorited === fl) {
                        show = true;
                    }
                    // special
                    if (cmd[1].substring(0, 2) === "sp" && activity.special === fl) {
                        show = true;
                    }
                    // admin
                    if (cmd[1].substring(0, 2) === "ad" && activity.administrative === fl) {
                        show = true;
                        showAdminact = true;
                    }
                    // presign
                    if (cmd[1].substring(0, 1) === "p" && activity.presign === fl) {
                        show = true;
                    }
                    // sticky
                    if (cmd[1].substring(0, 2) === "st" && activity.sticky === fl) {
                        show = true;
                    }
                    // full
                    if (cmd[1].substring(0, 1) === "f" && (activity.roster.capacity >= activity.roster.count) === fl) {
                        show = true;
                    }
                    // open
                    if (cmd[1].substring(0, 2) === "op" && (activity.roster.count < activity.roster.capacity) === fl) {
                        show = true;
                    }
                    // selected
                    if (cmd[1].substring(0, 2) === "se" && activity.selected === fl) {
                        show = true;
                        showAdminact = true;
                    }
                } else if (inv) {
                    show = !show;
                }

                queries.push(search);
                shows.push(show);
            }
            show = false;

            // console.debug("activity", aid, shows);
            /* imply OR:
            if (shows.indexOf("and") !== -1) {
                var nshows = [];
                for (var i in shows) {
                    if (shows[i] === "and") {
                        console.debug("AND:", i);
                        i = parseInt(i);
                        if (i-1 >= 0 && i+1 < shows.length) {
                            console.debug("andqs:", shows[i-1], shows[i+1]);
                            nshows.push(shows[i-1] && shows[i+1]);
                        }
                    }
                }
                show = true;
                for (i in nshows) {
                    if (!nshows[i]) show = false;
                }
            } */

            if (queries.indexOf("or") !== -1) {
                var nshows = [];
                for (var i in queries) {
                    if (queries[i] === "or") {
                        //console.debug("OR:", i);
                        i = parseInt(i);
                        if (i - 1 >= 0 && i + 1 < queries.length) {
                            //console.debug("orqs:", queries[i-1], queries[i+1]);
                            //console.debug("orqs:", shows[i-1], shows[i+1]);
                            nshows.push(shows[i - 1] || shows[i + 1]);
                        }
                    }
                }

                for (var i in nshows) {
                    if (nshows[i]) show = true;
                }
            } else {
                /* imply OR:
                for (i in shows) {
                    if (shows[i]) {show = true;}
                }
                */

                /* imply AND */
                show = true;
                for (i in shows) {
                    if (!shows[i]) show = false;
                }
            }

            if (show) {
                results.push(aid);
            }
        });

        // console.log("results:", results);

        $("#activity-list li[data-activity-id]").each(function() {
            var aid = $(this).data("activity-id");

            if (results.indexOf(aid) !== -1) {
                $(this).removeClass("search-hide").addClass("search-show");
            } else {
                $(this).addClass("search-hide").removeClass("search-show");
            }
        });

        /* hide headers with no activities */
        $("#activity-list > ul[data-header]").each(function() {
            var vis = $("li:not(.search-hide)[data-activity-id]", $(this));
            var cat = $(this).attr("data-header");
            var hideUl = (cat !== "all-header");
            var sticky = $(".sticky-header." + cat);
            var hideHeader = !sticky.hasClass("no-activities");
            console.log(vis.size(), cat);

            if (vis.size() === 0) {
                if (hideUl) $(this).hide();
                if (hideHeader) sticky.hide();
            } else {
                if (hideUl) $(this).show();
                if (hideHeader) sticky.show();
            }
        });

        if (results.length === 0) {
            // No results
            $("#activity-list ul.search-noresults").show();
        } else {
            $("#activity-list ul.search-noresults").hide();
        }

        if (showAdminact) {
            $("#activity-list").addClass("show-administrative");
        } else {
            $("#activity-list").removeClass("show-administrative");
        }

        var tm = (+new Date - _st);
        if (searchDebug) {
            console.info(searchSplit, "search time:", tm);
        }
    };

    $(".search-wrapper input")
        .removeAttr("disabled")
        .keyup(eighthSearch)
        .on("search", eighthSearch);

    function badgeClickUpdate() {
        $(".badge[data-append-search]").click(function() {
            var app = $(this).attr("data-append-search");
            var inp = $(".search-wrapper input");
            var v = inp.val();
            console.debug("adding tag:", app, v);
            if (v.indexOf(app) === -1) {
                inp.val(v + (v.length > 0 ? " " : "") + app);
            }
            inp.keyup();
        });
    };

    badgeClickUpdate();
});
