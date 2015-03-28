var eighth = {};
var previousSelection = $("#activity-list li")[0];

$(function() {
    eighth.Activity = Backbone.Model.extend({
        idAttribute: "id"
    });

    eighth.ActivityList = Backbone.Collection.extend({
        model: eighth.Activity
    });

    loadModels();

    eighth.ActivityDetailView = Backbone.View.extend({
        initialize: function(){
            _.bindAll(this, "render");

            this.template = _.template($("#activity-details-template").html());
        },

        render: function(){
            var container = this.options.viewContainer,
                activity = this.model,
                renderedContent = this.template(this.model.toJSON());
            container.html(renderedContent);
            return this;
        }
    });

    eighth.ActivityView = Backbone.View.extend({
        tagName: "li",

        events: {
          "click": "showDetail"
        },

        initialize: function(){
          _.bindAll(this, "render", "showDetail");
        },

        render: function(){
            $(this.el).html(this.model.get("name"));
            return this;
        },

        showDetail: function(e) {

            $(previousSelection).removeClass("selected");

            var $target = $(e.target);
            if (!$target.is("li")) {
                $target = $target.parents("li");
            }

            if(!$target.attr("data-activity-id")) {
                return;
            }

            $target.addClass("selected");
            previousSelection = $target;

            activityDetailView = new eighth.ActivityDetailView({
                model: this.model,
                viewContainer: $("#activity-detail")
            });

            $("#activity-detail").data("aid", activityDetailView.model.id);

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
            $("#signup-button").click(signupClickHandler);
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
                    $(".current-day .both-blocks .selected-activity").text("");
                    $(".current-day .both-blocks").removeClass("both-blocks");

                    $(".current-day .blocks a[data-bid='" + bid + "'] .block .selected-activity").text(activity.attributes.name).attr("title", activity.attributes.name);
                } else {
                    $(".current-day .selected-activity").text(activity.attributes.name).attr("title", activity.attributes.name);
                    $(".current-day .block").addClass("both-blocks");
                }

                $(".block.cancelled").removeClass("cancelled");

                var selectedActivity = activityModels.filter(function(a){return a.attributes.selected == true});
                _.each(selectedActivity, function(a){
                    a.attributes.selected = false;
                    a.attributes.roster.count -= 1;
                });

                activity.attributes.selected = true;
                activity.attributes.roster.count += 1;

                activityDetailView.render()
            },
            error: function(xhr, status, error) {
                var content_type = xhr.getResponseHeader("content-type");
                if (xhr.status == 403 &&
                    (content_type == "text/plain" ||
                     content_type.indexOf("text/plain;") == 0 ||
                     content_type == "text/html" ||
                     content_type.indexOf("text/html;") == 0)) {

                    $(".error-feedback").html(xhr.responseText);
                    if (showForceButton) {
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

    $("#activity-list li").each(function(index) {
        var id = $(this).data("activity-id");
        var view = new eighth.ActivityView({
            el: this,
            model: activityModels.get(id)
        });
    })


    eighth.ActivityListView = Backbone.View.extend({
        el: $("#activity-list"),

        initialize: function() {
            _.bindAll(this, "render");

            this.activityList = activityModels;
        },

        render: function() {
            var self = this;
            _(this.activityList.models).each(function(activity){
                var activityView = new eighth.ActivityView({
                    model: activity
                });

                $("ul", this.el).append(activityView.render().el);
            }, this);
        }
    });

    var activityListView = new eighth.ActivityListView();
});
