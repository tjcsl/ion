/* global $ */
var eighth = {};

$(function() {
    eighth.Activity = Backbone.Model.extend({
        idAttribute: "id"
    });

    eighth.ActivityList = Backbone.Collection.extend({
        model: eighth.Activity,
        comparator: function(a1, a2) {
            // float special activities to top
            // if (a1.attributes.special && !a2.attributes.special) {return -1;}
            // if (!a1.attributes.special && a2.attributes.special) {return 1;}

            var n1 = a1.attributes.name.toLowerCase(),
                n2 = a2.attributes.name.toLowerCase();
            if (n1 < n2) return -1;
            if (n1 > n2) return 1;
            return 0;
        }
    });

    loadModels();

    var waitlistedActivity = activityModels.filter(function(a) {
        return a.attributes.waitlisted === true;
    });
    window.currentWaitlist = waitlistedActivity.map(function(a) {
        return a.attributes.name;
    }).join(", ") || false;

    eighth.ActivityDetailView = Backbone.View.extend({
        el: $("#activity-detail"),

        initialize: function() {
            _.bindAll(this, "render");
            this.template = _.template($("#activity-details-template").html());
        },

        events: {
            "click button#signup-button": "signupClickHandler",
            "click button#waitlist-button": "waitlistClickHandler",
            "click button#leave-waitlist": "leaveWaitlistClickHandler",
            "click a#roster-button": "rosterClickHandler",
            "click a#roster-waitlist-button": "rosterWaitlistClickHandler",
            "click button#close-activity-detail": "closeActivityDetail"
        },

        render: function() {
            var container = this.options.viewContainer,
                renderedContent = this.template(this.model.toJSON());
            container.html(renderedContent);
            return this;
        },

        signupClickHandler: function(e) {
            var target = e.target;
            $(target).attr("disabled", true);
            var spinnerEl = document.getElementById("signup-spinner");
            var spinner = new Spinner(spinnerOptions).spin(spinnerEl);
            var aid = $(this.el).data("aid"),
                bid = $(this.el).data("bid"),
                uid = $(this.el).data("uid");

            eighth.signUp(uid, bid, aid, function() {
                $(target).removeAttr("disabled");
                spinner.spin(false);
            });
        },

        waitlistClickHandler: function(e) {
            var target = e.target;
            $(target).attr("disabled", true);
            var aid = aid = $(this.el).data("aid"),
                bid = $(this.el).data("bid"),
                uid = $(this.el).data("uid");
            eighth.waitlistAdd(uid, bid, aid, function() {
                $(target).removeAttr("disabled");
            });
        },

        leaveWaitlistClickHandler: function(e) {
            var target = e.target;
            $(target).attr("disabled", true);
            var aid = aid = $(this.el).data("aid"),
                bid = $(this.el).data("bid"),
                uid = $(this.el).data("uid");
            eighth.leaveWaitlist(uid, bid, aid, function() {
                $(target).removeAttr("disabled");
            });
        },

        rosterClickHandler: function(e) {
            e.preventDefault();
            var target = e.target;
            console.log(target);
            var container = $("#roster-section");

            if ($.trim(container.html()) === '') {
                var spinnerEl = document.getElementById("signup-spinner");
                var spinner = new Spinner(spinnerOptions).spin(spinnerEl);
                var schact_id = this.model.attributes.scheduled_activity.id;
                console.debug("Load roster for scheduled activity", schact_id);
                var endpoint = $(target).data("endpoint");

                container.load(endpoint + "/" + schact_id, {}, function(resp) {
                    spinner.spin(false);
                    $(target).text("Close Roster");
                });
            } else {
                container.empty();
                $(target).text("View Roster");
            }
        },

        rosterWaitlistClickHandler: function(e) {
            e.preventDefault();
            var target = e.target;
            console.log(target);
            var container = $("#waitlist-section");

            if ($.trim(container.html()) === '') {
                var spinnerEl = document.getElementById("signup-spinner");
                var spinner = new Spinner(spinnerOptions).spin(spinnerEl);
                var schact_id = this.model.attributes.scheduled_activity.id;
                console.debug("Load waitlist for scheduled activity", schact_id);
                var endpoint = $(target).data("endpoint");

                container.load(endpoint + "/" + schact_id, {}, function(resp) {
                    spinner.spin(false);
                    $(target).text("Close Waitlist");
                });
            } else {
                container.empty();
                $(target).text("View Waitlist");
            }
        },

        closeActivityDetail: function(e) {
            e.preventDefault();
            $(".primary-content.eighth-signup").removeClass("activity-detail-selected");
            $("#activity-detail").removeClass("selected");
            $("li.selected[data-activity-id]").removeClass("selected");
        }
    });

    eighth.ActivityListRowView = Backbone.View.extend({
        tagName: "li",
        attributes: function() {
            return {
                "data-activity-id": this.model.id,
                "data-scheduled-activity-id": this.model.scheduled_activity,
                "data-user-restricted": this.model.attributes.restricted_for_user,
                "data-administrative": this.model.attributes.administrative,
                "data-cancelled": this.model.attributes.cancelled,
                "data-favorited": this.model.attributes.favorited,
                "data-recommended": this.model.attributes.is_recommended,
                "data-sticky": this.model.attributes.sticky
            };
        },

        events: {
            "click": "showDetail"
        },

        initialize: function() {
            _.bindAll(this, "render", "showDetail");
            this.template = _.template($("#activity-list-row-template").html());
        },

        render: function() {
            this.$el.html(this.template(this.model.toJSON()));
            return this;
        },

        showDetail: function(e) {
            $("#activity-list li[data-activity-id].selected").removeClass("selected");
            var $target = $(e.target);
            if (!$target.is("li")) $target = $target.parents("li");

            if (!$target.attr("data-activity-id")) return;

            $target.addClass("selected");

            if (window.activityDetailView) {
                window.activityDetailView.model = this.model;
            } else {
                window.activityDetailView = new eighth.ActivityDetailView({
                    model: this.model,
                    viewContainer: $("#activity-detail")
                });
            }

            $("#activity-detail").data("aid", window.activityDetailView.model.id);
            $("#activity-detail").parent().addClass("activity-detail-selected");
            $("#activity-detail").addClass("selected");

            window.activityDetailView.render();

            initUIElementBehavior();

            if (typeof badgeClickUpdate !== "undefined") {
                badgeClickUpdate();
            }

            /* remove ?activity= from URL if able */
            if (location.search.substring(0, 10) === "?activity=" && history.pushState) {
                history.pushState(null, null, location.href.split("?activity=")[0]);
            }
        }
    });

    eighth.signUp = function(uid, bid, aid, callback) {
        var queryParams = $("#signup-button").hasClass("force") ? "?force" : "";
        $.ajax({
            url: $("#activity-detail").data("signup-endpoint") + queryParams,
            type: "POST",
            data: {
                "uid": uid,
                "bid": bid,
                "aid": aid
            },
            success: function(response) {
                var activity = activityModels.get(aid);

                if (response.indexOf("added to waitlist") === -1) {
                    // If:
                    // - The signup succeeded
                    // - The user is signing themselves up
                    // - They have less then 40 minutes until signups close
                    // - They are not going to be redirected when they finish signing up
                    // - They are not already signed up for an activity ('.block.active-block .selected-activity .no-activity-selected' exists)
                    // Then ask them to sign up sooner.
                    if(response.toLowerCase().indexOf("successfully signed up") != -1
                       && window.isSelfSignup
                       && window.signupTime && window.signupTime - new Date() < 40 * 60 * 1000
                       && !window.next_url
                       && $(".block.active-block .selected-activity .no-activity-selected").length) {
                        Messenger().info({
                            message: 'In the future, please sign up for eighth period activities sooner.',
                            hideAfter: 5,
                            showCloseButton: false
                        });
                    }

                    if (!activity.attributes.both_blocks) {
                        $(".current-day .both-blocks .selected-activity").html("<span class='no-activity-selected'>\nNo activity selected</span>").attr("title", "");
                        $(".current-day .both-blocks").removeClass("both-blocks");
                        $(".current-day .blocks a[data-bid='" + bid + "'] .block .selected-activity").text("\n" + $('<textarea>').html(activity.attributes.name_with_flags_for_user).text()).attr("title", activity.attributes.name_with_flags_for_user);
                    } else {
                        $(".current-day .selected-activity").text("\n" + $('<textarea>').html(activity.attributes.name_with_flags_for_user).text()).attr("title", activity.attributes.name_with_flags_for_user);
                        $(".current-day .block").addClass("both-blocks");
                    }

                    var changed_activities = response.match(new RegExp('Your signup for .* on .* was removed', 'g'));

                    if (changed_activities !== null) {
                        for (var i = 0; i < changed_activities.length; i++) {
                            try {
                                var evnt = changed_activities[i];
                                console.debug(evnt);
                                var act = evnt.split('Your signup for ')[1].split(' on ');
                                var blk = act[1].split(' was removed')[0];
                                act = act[0];
                                console.info(act, blk);

                                $(".days-container .day .block").each(function() {
                                    var sa_blk = $(this).attr("title");
                                    var sa_act = $(".selected-activity", $(this)).attr("title");
                                    console.debug(sa_blk, sa_act);
                                    if (sa_blk === blk && sa_act === act) {
                                        console.log("Found changed activity:", blk, act);
                                        $(".selected-activity", $(this)).html("<span class='no-activity-selected'>\nNo activity selected</span>").attr("title", "");
                                    }
                                });
                            } catch (e) {
                                console.error("An error occurred updating your current signups.", e);
                            }
                        }
                    }

                    $(".active-block.cancelled").removeClass("cancelled");

                    if (!activity.attributes.both_blocks) {
                        $(".current-day .blocks a[data-bid='" + bid + "'] .fa-exclamation-circle").css("display", "none");
                        $(".current-day .blocks a[data-bid!='" + bid + "'] .fa-exclamation-circle").each(function() {
                            if($(this).closest(".block").find(".selected-activity .no-activity-selected").length) {
                                $(this).css("display", "");
                            }
                            else {
                                $(this).css("display", "none");
                            }
                        });
                    } else {
                        $(".current-day .block-letter .fa-exclamation-circle").css("display", "none");
                    }


                    var selectedActivity = activityModels.filter(function(a) {
                        return a.attributes.selected === true
                    });

                    _.each(selectedActivity, function(a) {
                        a.attributes.selected = false;
                        a.attributes.roster.count -= 1;
                    });

                    activity.attributes.roster.count += 1;
                    activity.attributes.waitlisted = false;
                    activity.attributes.selected = true;
                    activity.attributes.display_text = response.replace(new RegExp('\r?\n', 'g'), '<br>');
                }
                else {
                    var waitlistedActivity = activityModels.filter(function(a) {
                        return a.attributes.waitlisted === true
                    });
                    _.each(waitlistedActivity, function(a) {
                        a.attributes.waitlisted = false;
                        a.attributes.waitlist_count -= 1;
                    });
                    $(".current-day .block.active-block .block-letter").toggleClass("waitlist", true);
                    window.currentWaitlist = activity.attributes.name;
                    activity.attributes.waitlist_count += 1;
                    activity.attributes.waitlist_position = activity.attributes.waitlist_count;
                    activity.attributes.waitlisted = true;
                }


                activityDetailView.render();
                activityListView.render();

                var $container = $(".primary-content.eighth-signup");
                var next_url = $container.attr("data-next-url");

                if (next_url) location.href = next_url;
            },
            error: function(xhr, status, error) {
                var content_type = xhr.getResponseHeader("content-type");

                if (xhr.status === 403 &&
                    (content_type === "text/plain" ||
                        content_type.indexOf("text/plain;") === 0 ||
                        content_type === "text/html" ||
                        content_type.indexOf("text/html;") === 0)) {

                    $(".error-feedback").html(xhr.responseText);

                    if (isEighthAdmin) {
                        $("#signup-button").addClass("force");
                        $("#signup-button").text("Force Sign Up");
                    }

                } else if (xhr.status === 401) {
                    location.reload();
                } else {
                    console.error(xhr.responseText);

                    if (xhr.status === 401) {
                        $(".error-feedback").html("You must log in to sign up for this activity.");
                        window.location.replace("/login?next=" + window.location.pathname);
                    } else {
                        $(".error-feedback").html("There was an error signing you up for this activity.");
                    }
                }
            },
            complete: callback
        });
    };

    eighth.waitlistAdd = function(uid, bid, aid, callback) {
        $.ajax({
            url: $("#activity-detail").data("signup-endpoint") + "?add_to_waitlist=1",
            type: "POST",
            data: {
                "uid": uid,
                "bid": bid,
                "aid": aid
            },
            success: function() {
                var activity = activityModels.get(aid);

                var waitlistedActivity = activityModels.filter(function(a) {
                    return a.attributes.waitlisted === true
                });
                _.each(waitlistedActivity, function(a) {
                    a.attributes.waitlisted = false;
                    a.attributes.waitlist_count -= 1;
                });
                $(".current-day .block.active-block .block-letter").toggleClass("waitlist", true);
                window.currentWaitlist = activity.attributes.name;
                activity.attributes.waitlist_count += 1;
                activity.attributes.waitlist_position = activity.attributes.waitlist_count;
                activity.attributes.waitlisted = true;

                activityDetailView.render();
                activityListView.render();

                var $container = $(".primary-content.eighth-signup");
                var next_url = $container.attr("data-next-url");

                if (next_url) location.href = next_url;
            },
            error: function(xhr, status, error) {
                var content_type = xhr.getResponseHeader("content-type");

                if (xhr.status === 403 &&
                    (content_type === "text/plain" ||
                        content_type.indexOf("text/plain;") === 0 ||
                        content_type === "text/html" ||
                        content_type.indexOf("text/html;") === 0)) {

                    $(".error-feedback").html(xhr.responseText);

                } else if (xhr.status === 401) {
                    location.reload();
                } else {
                    console.error(xhr.responseText);

                    if (xhr.status === 401) {
                        $(".error-feedback").html("You must log in to sign up for this activity.");
                        window.location.replace("/login?next=" + window.location.pathname);
                    } else {
                        $(".error-feedback").html("There was an error joining the waitlist for this activity.");
                    }
                }
            },
            complete: callback
        });
    };
    eighth.leaveWaitlist = function(uid, bid, aid, callback) {
        $.ajax({
            url: $("#activity-detail").data("leave-waitlist-endpoint"),
            type: "POST",
            data: {
                "uid": uid,
                "bid": bid,
                "aid": aid
            },
            success: function() {
                var activity = activityModels.get(aid);

                activity.attributes.waitlisted = false;
                activity.attributes.waitlist_count -= 1;
                activity.attributes.waitlist_position = 0;
                $(".current-day .block.active-block .block-letter").toggleClass("waitlist", false);
                window.currentWaitlist = false;

                activityDetailView.render();
                activityListView.render();

                $("#leave-waitlist").hide();
            },
            error: function(xhr, status, error) {
                var content_type = xhr.getResponseHeader("content-type");

                if (xhr.status === 403 &&
                    (content_type === "text/plain" ||
                        content_type.indexOf("text/plain;") === 0 ||
                        content_type === "text/html" ||
                        content_type.indexOf("text/html;") === 0)) {

                    $(".error-feedback").html(xhr.responseText);

                } else if (xhr.status === 401) {
                    location.reload();
                } else {
                    console.error(xhr.responseText);

                    if (xhr.status === 401) {
                        $(".error-feedback").html("You must log in to sign up for this activity.");
                        window.location.replace("/login?next=" + window.location.pathname);
                    } else {
                        $(".error-feedback").html("There was an error signing you up for this activity.");
                    }
                }
            },
            complete: callback
        });
    };

    eighth.ActivityListView = Backbone.View.extend({
        el: $("#activity-list"),

        initialize: function() {
            this.rowViews = [];
            _.bindAll(this, "render");
            this.activities = activityModels.sort();
        },

        render: function() {
            var prevSelectedInFavorites = $("li[data-activity-id].selected").parent().hasClass("favorite-activities");
            var prevSelectedAid = $("li[data-activity-id].selected").data("activity-id");
            var rowViews = this.rowViews;

            while (rowViews.length > 0) {
                rowViews.pop().remove();
            }

            var renderActivitiesInContainer = function(models, $container) {
                $container.html("");
                _.each(models, function(model) {
                    var activityListRowView = new eighth.ActivityListRowView({
                        model: model
                    });
                    rowViews.push(activityListRowView);

                    $container.append(activityListRowView.render().el);
                }, this);
            }

            renderActivitiesInContainer(this.activities.models, $(".all-activities", this.el));

            var favorites = _.filter(this.activities.models, function(activity) {
                return activity.attributes.favorited;
            });

            renderActivitiesInContainer(favorites, $(".favorite-activities", this.el));

            if (favorites.length === 0) {
                $(".favorites-header").addClass("hidden");
            } else {
                $(".favorites-header").removeClass("hidden");
            }

            var specials = _.filter(this.activities.models, function(activity) {
                return activity.attributes.special;
            });

            renderActivitiesInContainer(specials, $(".special-activities", this.el));

            if (specials.length === 0) {
                $(".special-header").addClass("no-activities");
            } else {
                $(".special-header").removeClass("no-activities");
            }

            var recommendeds = _.filter(this.activities.models, function(activity) {
                return activity.attributes.is_recommended;
            });

            renderActivitiesInContainer(recommendeds, $(".recommended-activities", this.el));

            if (recommendeds.length === 0) {
                $(".recommended-header").addClass("no-activities");
            } else {
                $(".recommended-header").removeClass("no-activities");
            }

            if (!$("#activity-picker").hasClass("different-user")) {
                var view = this;

                $(".activity-icon.fav").click(function(event) {
                    var $icon = $(this);
                    var aid = $(this).parent().parent().data("activity-id");
                    var model = view.activities.get(aid);

                    $("#activity-list").scrollTop($("#activity-list").scrollTop() + ($(this).hasClass("fav-sel") ? -26 : 26));

                    model.attributes.favorited = !model.attributes.favorited;
                    view.render();

                    $("#activity-picker .search-wrapper input").val("").trigger("keyup");

                    $.ajax({
                        url: $("#activity-list").data("toggle-favorite-endpoint"),
                        type: "POST",
                        data: {
                            "aid": aid
                        },
                        error: function(xhr, status, error) {
                            console.error(xhr.responseText);
                            model.attributes.favorited = !model.attributes.favorited;
                            view.render();
                            alert("There was an error favoriting this activity. Try reloading the page.");
                        }
                    });

                    event.stopPropagation();
                })
            }

            if (prevSelectedAid !== null) {
                if (prevSelectedInFavorites) {
                    $("#activity-list .favorite-activities li[data-activity-id=" + prevSelectedAid + "]").addClass("selected");
                } else {
                    $("#activity-list .all-activities li[data-activity-id=" + prevSelectedAid + "]").addClass("selected");
                }
            }

            window.initEighthResponsive();
        }
    });

    window.activityListView = new eighth.ActivityListView();
    activityListView.render();

    $("button#unsignup-button").click(function() {
        var uid = $(this).attr("data-uid"),
            bid = $(this).attr("data-bid");
        var force = $(this).attr("force");

        var ths = $(this);
        if(confirm("Remove signups for all blocks?")) {
            $.ajax({
                url: $("#activity-detail").data("signup-endpoint"),
                type: "POST",
                data: {
                    "uid": uid,
                    "bid": bid,
                    "unsignup": true,
                    force: force
                },
                success: function(response) {
                    if (response) {
                        alert($("<div>" + response + "</div>").text());
                    }
                    console.error(response);
                    location = $(".eighth-profile-signup").data("next-url");
                },
                error: function(response, error) {
                    window.r = response;
                    if (response.responseText) {
                        alert($("<div>" + response.statusText + ": " + response.responseText + "</div>").text());
                    }
                    console.error(response);
                    ths.attr("force", true);
                    ths.html(ths.html() + " (Force)");
                }
            });
        }
    });
});
