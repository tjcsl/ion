$(document).ready(function() {

    eighthSearch = function() {
        var _st = +new Date();
        var searchStr = $(this).val().toLowerCase();
        var searchSplit = $.trim(searchStr).split(" ");

        // console.log("query:", searchStr);

        var results = [];
        var activities = window.activityModels._byId;

        $("#activity-list li[data-activity-id]").each(function() {
            var aid = $(this).data("activity-id");
            var activity = activities[aid].attributes;

            var shows = [];

            for(sp in searchSplit) {
                var search = searchSplit[sp];

                // blank entry
                if(search.length < 1) {
                    show = true;
                    results.push(aid);
                    continue; // skip
                }

                // - = inverse
                if(search.substring(0, 1) == "-") {
                    console.log("INVERSE");
                    search = search.substring(1);
                    var inv = true;
                } else {
                    var inv = false;
                }

                var show = false;

                // aids
                if(parseInt(search) == parseInt(aid)) {
                    show = true;
                }
                // name + comments
                if(activity.name_with_flags_for_user.toLowerCase().indexOf(search) != -1) {
                    show = true;
                }
                // sponsors
                for(sp in activity.sponsors) {
                    if(activity.sponsors[sp].toLowerCase().indexOf(search) != -1) {
                        show = true;
                    }
                }
                // rooms
                for(rm in activity.rooms) {
                    if(activity.rooms[rm].toLowerCase().indexOf(search) != -1) {
                        show = true;
                    }
                }

                var cmd = search.split(":");
                if(cmd.length > 1) {
                    // not: = inverse
                    var fl = ((cmd[0] == "not" || (cmd[0] == "is" && inv)) ? false : true);
                    // restricted
                    if(cmd[1].substring(0,1) == "r" && activity.restricted == fl) {
                        show = true;
                    }
                    // cancelled
                    if(cmd[1].substring(0,1) == "c" && activity.cancelled == fl) {
                        show = true;
                    }
                    // bothblocks
                    if(cmd[1].substring(0,1) == "b" && activity.both_blocks == fl) {
                        show = true;
                    }
                    // favorite
                    if(cmd[1].substring(0,1) == "f" && activity.favorited == fl) {
                        show = true;
                    }
                    // special
                    if(cmd[1].substring(0,2) == "sp" && activity.special == fl) {
                        show = true;
                    }
                    // admin
                    if(cmd[1].substring(0,1) == "a" && activity.administrative == fl) {
                        show = true;
                    }
                    // sticky
                    if(cmd[1].substring(0,2) == "st" && activity.sticky == fl) {
                        show = true;
                    }
                    // full
                    if(cmd[1].substring(0,1) == "f" && (activity.roster.capacity >= activity.roster.count) == fl) {
                        show = true;
                    }
                    // open
                    if(cmd[1].substring(0,1) == "o" && (activity.roster.count < activity.roster.capacity) == fl) {
                        show = true;
                    }
                    // selected
                    if(cmd[1].substring(0,2) == "se" && activity.selected == fl) {
                        show = true;
                    }
                } else if(inv) {
                    show = !show;
                }

                if(search == "and") {
                    shows.push(search);
                } else {
                    shows.push(show);
                }
            }
            var show = false;

            console.debug("activity", aid, shows);
            if(shows.indexOf("and") != -1) {
                var nshows = [];
                for(i in shows) {
                    if(shows[i] == "and") {
                        console.debug("AND:", i);
                        i = parseInt(i);
                        if(i-1 >= 0 && i+1 < shows.length) {
                            console.debug("andqs:", shows[i-1], shows[i+1])
                            nshows.push(shows[i-1] && shows[i+1]);
                        }
                    }
                }
                show = true;
                for(i in nshows) {
                    if(!nshows[i]) show = false;
                }
            } else {
                for(i in shows) {
                    if(shows[i]) show = true;
                }
            }

            if(show) results.push(aid);
        });

        // console.log("results:", results);

        $("#activity-list li[data-activity-id]").each(function() {
            var aid = $(this).data("activity-id");

            if(results.indexOf(aid) != -1) {
                $(this).removeClass("search-hide").addClass("search-show");
            } else {
                $(this).addClass("search-hide").removeClass("search-show");
            }

        });

        if(results.length == 0) {
            // No results
            $("#activity-list ul.search-noresults").show();
        } else {
            $("#activity-list ul.search-noresults").hide();
        }

        console.debug("time:", +new Date - _st);

    }

    $(".search-wrapper input")
        .removeAttr("disabled")
        .on("keyup", eighthSearch)
        .on("search", eighthSearch);
});
