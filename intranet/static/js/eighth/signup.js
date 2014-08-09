var eighth = {};
var previousSelection = $("#activity-list li")[0];

$(function() {

    // eighth.signUp = function(bid, aid) {
    //     $.post("/eighth/signup/" + bid, {
    //         "bid": bid,
    //         "aid": aid,
    //         "confirm": true
    //     }, function(d) {
    //         if(d.trim() == "success") {
    //             console.log("Successfully signed up for "+aid+" on "+bid);
    //             $d = $("#activity-detail[data-aid="+aid+"]");
    //             $c = $("li.day>a[data-bid="+bid+"]>div");
    //             // Replace the text on the day selector
    //             $c.html($c.html().replace(
    //                 $c.html().split("</span>")[1].trim(),
    //                 $("h3", $d).html().trim()
    //             ));
    //             $("#activity-list li.signed-up").removeClass("signed-up");
    //             $("#activity-list li[data-activity-id="+aid+"]").addClass("signed-up");
    //             $("#signup-spinner-container")
    //                 .html("<i class='icon-ok' style='color: green; zoom: 1.5' />")
    //                 .css("margin-left","2px");
    //         } else alert(d);
    //     })
    // };

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
            console.log(e.target);
            if (!$target.is("li")) {
                $target = $target.parents("li");
            }

            $target.addClass("selected");
            previousSelection = $target;

            activityDetailView = new eighth.ActivityDetailView({
                model: this.model,
                viewContainer: $("#activity-detail")
            });

            $("#activity-detail").attr("data-aid", activityDetailView.model.id);

            activityDetailView.render();
            $("#signup-button").click(function(event) {
                $(this).unbind(event);
                var target = document.getElementById("signup-spinner");
                var spinner = new Spinner(spinnerOptions).spin(target);
                var aid = $("#activity-detail").attr("data-aid");
                var bid = $("#activity-detail").attr("data-bid");
                // eighth.signUp(bid, aid);

            });
        }
    });

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
