var eighth = {};

$(function() {
    eighth.Activity = Backbone.Model.extend({
        idAttribute: "id"
    });

    eighth.ActivityList = Backbone.Collection.extend({
        model: eighth.Activity,
        comparator: function(a1, a2) {
            if (a1.attributes.special && !a2.attributes.special) return -1;
            if (!a1.attributes.special && a2.attributes.special) return 1;

            var n1 = a1.attributes.name.toLowerCase(),
                n2 = a2.attributes.name.toLowerCase();
            if (n1 < n2) return -1;
            if (n1 > n2) return 1;
            return 0;
        }
    });

    loadModels();

    eighth.ActivityDetailView = Backbone.View.extend({
        initialize: function(){
            _.bindAll(this, "render");

            this.template = _.template($("#activity-details-template").html());
        },

        render: function(){
            var container = this.options.viewContainer,
                renderedContent = this.template(this.model.toJSON());
            container.html(renderedContent);
            return this;
        }
    });

    eighth.ActivityListRowView = Backbone.View.extend({
        tagName: "li",
        attributes: function(){
            return {
                "data-activity-id": this.model.id,
                "data-scheduled-activity-id": this.model.scheduled_activity,
                "data-user-restricted": this.model.attributes.restricted_for_user,
                "data-administrative": this.model.attributes.administrative,
                "data-cancelled": this.model.attributes.cancelled,
                "data-favorited": this.model.attributes.favorited,
                "data-sticky": this.model.attributes.sticky
            }
        },

        events: {
            "click": "showDetail"
        },

        initialize: function(){
          _.bindAll(this, "render", "showDetail");

          this.template = _.template($("#activity-list-row-template").html());
        },

        render: function(){
            this.$el.html(this.template(this.model.toJSON()));
            return this;
        },

        showDetail: function(e) {
            $("#activity-list li[data-activity-id].selected").removeClass("selected");
            var $target = $(e.target);
            if (!$target.is("li")) {
                $target = $target.parents("li");
            }

            if(!$target.attr("data-activity-id")) {
                return;
            }

            $target.addClass("selected");

            activityDetailView = new eighth.ActivityDetailView({
                model: this.model,
                viewContainer: $("#activity-detail")
            });

            $("#activity-detail").data("aid", activityDetailView.model.id);
            $("#activity-detail").addClass("selected");

            activityDetailView.render();

            initUIElementBehavior();

            var signupClickHandler = function() {
                $(this).unbind("click");
                var target = document.getElementById("signup-spinner");
                var spinner = new Spinner(spinnerOptions).spin(target);
                var aid = $("#activity-detail").data("aid");
                var bid = $("#activity-detail").data("bid");
                var uid = $("#activity-detail").data("uid");

                eighth.signUp(uid, bid, aid, function() {
                    $("#signup-button").click(signupClickHandler);
                    spinner.spin(false);
                });
            };

            var rosterClickHandler = function() {
                var schact_id = activityDetailView.model.attributes.scheduled_activity;
                console.debug("Load roster for scheduled activity", schact_id)
                var endpoint = $(this).parent().data("endpoint");
                var container = $(this).parent();
                $.get(endpoint + "/" + schact_id, {}, function(resp) {
                    container.html(resp);
                });
            }
            $("#signup-button").click(signupClickHandler);
            $("#roster-button").click(rosterClickHandler);
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
                if (!activity.attributes.both_blocks) {
                    $(".current-day .both-blocks .selected-activity").html("<span class='no-activity-selected'>\nNo activity selected</span>").attr("title", "");
                    $(".current-day .both-blocks").removeClass("both-blocks");

                    $(".current-day .blocks a[data-bid='" + bid + "'] .block .selected-activity").text("\n" + activity.attributes.name_with_flags_for_user).attr("title", activity.attributes.name_with_flags_for_user);
                } else {
                    $(".current-day .selected-activity").text("\n" + activity.attributes.name_with_flags_for_user).attr("title", activity.attributes.name_with_flags_for_user);
                    $(".current-day .block").addClass("both-blocks");
                }

                var changed_activities = response.match(new RegExp('Your signup for .* on .* was removed', 'g'));
                if(changed_activities != null) {
                    for(var i=0; i<changed_activities.length; i++) {
                        try {
                            var evnt = changed_activities[i];
                            console.debug(evnt);
                            var act = evnt.split('Your signup for ')[1].split(' on ');
                            var blk = act[1].split(' was removed');
                            act = act[0];
                            blk = blk[0];
                            console.info(act, blk);
                            $(".days-container .day .block").each(function() {
                                var sa_blk = $(this).attr("title");
                                var sa_act = $(".selected-activity", $(this)).attr("title");
                                console.debug(sa_blk, sa_act);
                                if(sa_blk == blk && sa_act == act) {
                                    console.log("Found changed activity:", blk, act);
                                    $(".selected-activity", $(this)).html("<span class='no-activity-selected'>\nNo activity selected</span>").attr("title", "");
                                }

                            });
                        } catch(e) {
                            console.error("An error occurred updating your current signups.");
                            console.error(e);
                        }
                    }

                }


                $(".active-block.cancelled").removeClass("cancelled");

                var selectedActivity = activityModels.filter(function(a){return a.attributes.selected == true});
                _.each(selectedActivity, function(a){
                    a.attributes.selected = false;
                    a.attributes.roster.count -= 1;
                });

                activity.attributes.selected = true;
                activity.attributes.roster.count += 1;
                activity.attributes.display_text = response.replace(new RegExp('\r?\n', 'g'), '<br />');

                activityDetailView.render();
                activityListView.render();


            },
            error: function(xhr, status, error) {
                var content_type = xhr.getResponseHeader("content-type");
                if (xhr.status == 403 &&
                    (content_type == "text/plain" ||
                     content_type.indexOf("text/plain;") == 0 ||
                     content_type == "text/html" ||
                     content_type.indexOf("text/html;") == 0)) {

                    $(".error-feedback").html(xhr.responseText);
                    if (isEighthAdmin) {
                        $("#signup-button").addClass("force");
                        $("#signup-button").text("Force Sign Up");
                    }
                } else {
                    console.error(xhr.responseText);
                    if (xhr.status == 401) {
                        $(".error-feedback").html("You must log in to sign up for this activity.")
                        window.location.replace("/login?next=" + window.location.pathname)
                    } else {
                        $(".error-feedback").html("There was an error signing you up for this activity.")
                    }
                }
            },
            complete: callback
        });
    };

    eighth.ActivityListView = Backbone.View.extend({
        el: $("#activity-list"),

        initialize: function() {
            _.bindAll(this, "render");

            this.activities = activityModels.sort();
        },

        render: function() {
            var prevSelectedInFavorites = $("li[data-activity-id].selected").parent().hasClass("favorite-activities");
            var prevSelectedAid = $("li[data-activity-id].selected").data("activity-id");

            var renderActivitiesInContainer = function(models, $container) {
                $container.html("");
                _.each(models, function(model){
                    var ActivityListRowView = new eighth.ActivityListRowView({
                        model: model
                    });

                    $container.append(ActivityListRowView.render().el);
                    // console.log(model.attributes.name);
                }, this);
            }

            renderActivitiesInContainer(this.activities.models, $(".all-activities", this.el))

            var favorites = _.filter(this.activities.models, function(activity) {
                return activity.attributes.favorited;
            });
            renderActivitiesInContainer(favorites, $(".favorite-activities", this.el));
            if (favorites.length == 0) {
                $(".favorites-header").addClass("hidden");
            } else {
                $(".favorites-header").removeClass("hidden");
            }

            if (!$("#activity-picker").hasClass("different-user")) {
                var view = this;
                $(".activity-icon.fav").click(function(event) {
                    var aid = $(this).parent().parent().data("activity-id");
                    var $icon = $(this);
                    var model = view.activities.get(aid);

                    $("#activity-list").scrollTop($("#activity-list").scrollTop() + ($(this).hasClass("fav-sel") ? -26 : 26));

                    model.attributes.favorited = !model.attributes.favorited;
                    view.render();

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
                            alert("There was an error favoriting this activity. Try reloading the page.")
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
    activityListView.render()
});
