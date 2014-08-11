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
        console.log(uid, bid, aid);

        $.ajax({
            url: $("#activity-detail").data("aid"),
            type: "POST",
            data: {
                "uid": uid,
                "bid": bid,
                "aid": aid
            },
            success: function(response) {
                var activity = activityModels.get(aid);
                $(".current-day .blocks a[data-bid='" + bid + "'] .block span")[0].nextSibling.data = "\n\n" + activity.attributes.name;

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
                console.error(xhr.responseText);
                // $("button").text("Error!");
                // setTimeout(function() {
                //     $(button).text("Delete Selected");
                // }, 1000);
            },
            complete: callback
        });

        // $.post("/eighth/signup", {
        //     "uid": uid,
        //     "bid": bid,
        //     "aid": aid
        // }, function(response) {
        //     if(d.trim() == "success") {
        //         console.log("Successfully signed up for "+aid+" on "+bid);
                // $d = $("#activity-detail[data-aid="+aid+"]");
                // $c = $("li.day>a[data-bid="+bid+"]>div");
                // // Replace the text on the day selector
                // $c.html($c.html().replace(
                //     $c.html().split("</span>")[1].trim(),
                //     $("h3", $d).html().trim()
                // ));
        //         $("#activity-list li.signed-up").removeClass("signed-up");
        //         $("#activity-list li[data-activity-id="+aid+"]").addClass("signed-up");
        //         $("#signup-spinner-container")
        //             .html("<i class='icon-ok' style='color: green; zoom: 1.5' />")
        //             .css("margin-left","2px");
        //     } else alert(d);
        // });
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
