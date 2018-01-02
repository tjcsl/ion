/* globals Messenger */
var bus = {};

$(function() {
    let base_url = window.location.host;

    bus.sendUpdate = function (data) {
        socket.send(JSON.stringify(data));
    };

    bus.Route = Backbone.Model.extend({
        defaults: {
            'id': '0',
            'status': 'o',
            'bus_number': 'No bus number set.',
            'route_name': 'Empty route'
        }
    });

    bus.RouteList = Backbone.Collection.extend({
        model: bus.Route
    });

    bus.StatusGroupModel = Backbone.Model.extend();

    bus.PersonalStatusView = Backbone.View.extend({
        initialize: function() {
            _.bindAll(this, 'render');
            this.template = _.template($('#personal-status').html());
        },
        render: function() {
            var container = this.$el,
                renderedContent = this.template(this.model.toJSON());
            container.html(renderedContent);
            return this;
        }
    });

    bus.ActionButtonView = Backbone.View.extend({
        initialize: function () {
            _.bindAll(this, 'render');
            this.template = _.template($('#action-button-view').html());
            this.icon = 'fa-search';
            this.text = 'search for bus';

            Backbone.on('selectEmptySpace', this.handleEmptySpace, this);
            Backbone.on('selectFilledSpace', this.handleFilledSpace, this);
            Backbone.on('deselectSpace', this.handleDeselectSpace, this);
        },
        render: function () {
            let data = {
                'icon': this.icon,
                'text': this.text
            };
            this.$el.html(this.template(data));
            console.log(data);
            return this;
        },
        handleEmptySpace: function () {
            console.log('hi');
            this.icon = 'fa-plus-square';
            this.text = 'assign bus';
            this.render();
        },
        handleFilledSpace: function () {
            console.log('hi');
            this.icon = 'fa-minus-square';
            this.text = 'unassign bus';
            this.render();
        },
        handleDeselectSpace: function () {
            console.log('hi');
            this.icon = 'fa-search';
            this.text = 'search for bus';
            this.render();
        }
    });

    bus.MapView = Backbone.View.extend({
        initialize: function () {
            _.bindAll(this, 'render');
            this.template = _.template($('#map-view').html());
            this.selected = null;
        },

        events: {
            'click path': 'selectSpace',
            'click': 'deselectSpace'
        },

        render: function (collection) {
            var container = this.$el,
                renderedContent = this.template({});
            container.html(renderedContent);
            console.log(container);
            var draw = SVG.adopt(container.find('svg')[0]);
            collection.forEach(function (route) {
                if (route.attributes.status === 'a' && route.attributes.space) {
                    var space = container.find(`#${route.attributes.space}`)[0];
                    if (space) {
                        let text = draw.text(route.attributes.route_name);
                        text.path(space.getAttribute('d'));
                        space.style.fill = '#FFD800';
                        $(space).data({
                            'filled': true,
                            'route': route.attributes
                        });
                    }
                }
            });
            return this;
        },

        selectSpace: function (e) {
            e.stopPropagation();
            if (this.selected) {
                this.selected.style.stroke = 'none';
                if (e.target === this.selected) {
                    this.deselectSpace(e);
                    return;
                }
            }
            const space = e.target;
            if (!$(space).data('filled')) {
                Backbone.trigger('selectEmptySpace');
                console.log('select empty');
            } else {
                Backbone.trigger('selectFilledSpace');
                console.log('select full');
            }
            space.style.stroke = 'black';
            this.selected = space;
        },

        deselectSpace: function (e) {
            if (this.selected) {
                this.selected.style.stroke = 'none';
                this.selected = null;
                Backbone.trigger('deselectSpace');
                console.log('deselect');
            }
        }
    });

    bus.RouteView = Backbone.View.extend({
        className: 'bus',
        initialize: function () {
            _.bindAll(this, 'render');
            this.template = _.template($('#route-view').html());
        },

        events: {
            'change select': 'update'
        },

        render: function () {
            this.$el.empty();
            this.$el.append(this.template(this.model.toJSON()));
            return this;
        },

        update: function () {
            let val = this.$el.children('select').val();
            bus.sendUpdate({
                id: this.model.attributes.id,
                status: val
            });
        }
    });

    bus.StatusGroupView = Backbone.View.extend({
        initialize: function () {
            _.bindAll(this, 'render');
            this.template = _.template($('#status-group-view').html());
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
        el: '.primary-content .info',

        initialize: function () {
            _.bindAll(this, 'render');
            this.on('wss:receive', this.update, this);
            this.categories = ['a', 'o', 'd'];
            this.routeList = new bus.RouteList();

            this.personalStatusView = new bus.PersonalStatusView();
            this.mapView = new bus.MapView();
            this.actionButtonView = new bus.ActionButtonView();
            // this.render();
        },

        render: function () {
            var container = this.$el;
            // renderedContent = this.template();
            container.children().detach();
            container.append(this.personalStatusView.render().el);
            container.append(this.actionButtonView.render().el);
            container.append(this.mapView.render(this.routeList).el);

            let statusGroups = this.routeList.groupBy('status');

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
            console.log(data);
            if (data.error) {
                Messenger().error(data.error);
                return;
            }
            this.routeList.reset(data.allRoutes);

            this.user_bus = this.routeList.find((route) => {
                if (data.userRouteId) {
                    return route.id === data.userRouteId;
                } else if (this.user_bus) {
                    return route.id === this.user_bus.id;
                }
            });

            console.log(this.user_bus);

            this.user_bus = this.user_bus ? this.user_bus : new bus.Route();
            this.personalStatusView.model = this.user_bus;

            console.log(this.user_bus);

            this.render();
        }
    });

    const protocol = (location.protocol.indexOf('s') > -1) ? 'wss' : 'ws';
    let socket = new ReconnectingWebSocket(`${protocol}://${base_url}/bus/`);
    let disconnected = false;
    window.appView = new bus.AppView();
    console.log('Connected');

    socket.onopen = () => {
        if (disconnected) {
            disconnected.update({
                message: 'Connection Restored',
                type: 'success',
                hideAfter: 3
            });
        }
    };

    socket.onmessage = (event) => {
        window.appView.trigger('wss:receive', JSON.parse(event.data));
    };

    socket.onclose = () => {
        console.log('disconnected');
        let msg = Messenger().error({
            message: 'Connection Lost',
            hideAfter: 0,
            showCloseButton: false
        });
        disconnected = msg;
    };

    // window.personalStatusView = new bus.personalStatusView();
});

