var eighth = {};

$(document).ready(function() {

    eighth.Activity = Backbone.Model.extend({
        idAttribute: "activity_id"
    });

    eighth.ActivityList = Backbone.Collection.extend({
        model: eighth.Activity
    });

    loadModels();

    eighth.ActivityDetailView = Backbone.View.extend({
        initialize: function(){
            _.bindAll(this, "render");

            this.template = _.template($('#activity-details-template').html());
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

        showDetail: function() {
            activityDetailView = new eighth.ActivityDetailView({
                model: this.model,
                viewContainer: $("#activity-detail")
            });

            activityDetailView.render();
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