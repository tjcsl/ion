/* globals Messenger */
var bus = {};

$(function() {
    let base_url = window.location.host;

    bus.sendUpdate = function (data) {
        socket.send(JSON.stringify(data));
    };

    bus.Route = Backbone.Model.extend({
        defaults: {
            "id": "0",
            "status": "o",
            "bus_number": "No bus number set.",
            "route_name": "Empty route"
        }
    });

    bus.RouteList = Backbone.Collection.extend({
        model: bus.Route
    });

    bus.StatusGroupModel = Backbone.Model.extend();

    bus.PersonalStatusView = Backbone.View.extend({
        initialize: function() {
            _.bindAll(this, "render");
            this.template = _.template($("#personal-status").html());
        },
        render: function() {
            var container = this.$el,
                renderedContent = this.template(this.model.toJSON());
            container.html(renderedContent);
            return this;
        }
    });

    bus.RouteView = Backbone.View.extend({
        className: "bus",
        initialize: function () {
            _.bindAll(this, "render");
            this.template = _.template($("#route-view").html());
        },

        events: {
            "change select": "update"
        },

        render: function () {
            this.$el.empty();
            this.$el.append(this.template(this.model.toJSON()));
            return this;
        },

        update: function () {
            let val = this.$el.children("select").val();
            bus.sendUpdate({
                id: this.model.attributes.id,
                status: val
            });
        }
    });

    bus.StatusGroupView = Backbone.View.extend({
        initialize: function () {
            _.bindAll(this, "render");
            this.template = _.template($("#status-group-view").html());
        },

        render: function () {
            var container = this.$el;
            container.empty();
            container.append(this.template(this.model.toJSON()));
            _.each(this.model.attributes.collection, function (route) {
                container.append(new bus.RouteView({model: route}).render().el);
            });
            return this;
        }
    });

    bus.AppView = Backbone.View.extend({
        el: ".primary-content",

        initialize: function () {
            _.bindAll(this, "render");
            this.on("wss:receive", this.update, this);
            this.categories = ["a", "o", "d"];
            this.routeList = new bus.RouteList();

            this.personalStatusView = new bus.PersonalStatusView();
            // this.render();
        },

        render: function () {
            var container = this.$el;
                // renderedContent = this.template();
            container.empty();
            container.append(this.personalStatusView.render().el);

            let statusGroups = this.routeList.groupBy("status");

            _.each(this.categories, function (cat) {
                let statusGroup = new bus.StatusGroupModel({
                    name: window.label_status_strings[cat].name,
                    empty_text: window.label_status_strings[cat].empty_text,
                    collection: statusGroups[cat] || []
                });
                container.append(new bus.StatusGroupView({model: statusGroup }).render().el);
            });

            // container.append(renderedContent);
            return this;
        },

        update: function (data) {
            console.log(data)
            if (data.error) {
                Messenger().error(data.error);
                return;
            }
            this.routeList.reset(data.allRoutes);

            this.user_bus = this.routeList.find((route) => {
                if (data.userRouteId)
                    return route.id === data.userRouteId;
                else if (this.user_bus)
                    return route.id === this.user_bus.id;
            });

            console.log(this.user_bus)

            this.user_bus = this.user_bus ? this.user_bus : new bus.Route();
            this.personalStatusView.model = this.user_bus;

            console.log(this.user_bus)

            this.render();
        }
    });

    let socket = new WebSocket(`wss://${base_url}/bus/`);
    window.appView = new bus.AppView();
    socket.onmessage = (event) => {
        window.appView.trigger("wss:receive", JSON.parse(event.data));
    };
    socket.onclose = () => {
        Messenger().error({
            message: "Connection Lost",
            hideAfter: 0,
            showCloseButton: false
        });
    };

    // window.personalStatusView = new bus.personalStatusView();
});

