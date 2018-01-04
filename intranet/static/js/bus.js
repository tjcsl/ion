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
        className: 'action-view',
        initialize: function () {
            _.bindAll(this, 'render');
            this.buttonTemplate = _.template($('#action-button-view').html());
            this.searchTemplate = _.template($('#search-widget-view').html());
            this.model = [];
            this.icon = 'fa-search';
            this.text = 'search for bus';
            this.action = 'search';

            this.clicked = false;
            this.hlBus = null;
            this.selected = null;

            Backbone.on('selectEmptySpace', this.handleEmptySpace, this);
            Backbone.on('selectFilledSpace', this.handleFilledSpace, this);
            Backbone.on('deselectSpace', this.handleDeselectSpace, this);
        },
        events: {
            'click .back-button': 'handleReturnClick',
            'click': 'handleAction',
            'change select': 'handleBusSelect'
        },
        render: function () {
            if (this.clicked) {
                return this.renderSearchView(this.model, this.action);
            } else {
                return this.renderButton();
            }
        },
        renderButton: function () {
            let data = {
                'icon': this.icon,
                'text': this.text
            };
            this.$el.html(this.buttonTemplate(data))
                    .removeClass('search-widget');
            return this;
        },
        renderSearchView: function (routeList, action) {
            var container = this.$el,
                renderedContent = this.searchTemplate();
            container.addClass('search-widget');
            container.html(renderedContent);
            let busList = [];
            if (action === 'search') {
                busList = routeList.filter(bus => bus.attributes.status === 'a')
                                   .map(bus => bus.attributes);
            } else {
                busList = routeList.filter(bus => bus.attributes.status !== 'a')
                                   .map(bus => bus.attributes);
            }
            container.find('select').selectize({
                'options': busList,
                'valueField': 'route_name',
                'labelField': 'route_name',
                'placeholder': action,
                'searchField': 'route_name'
            })[0].selectize.focus();
            return this;
        },
        handleBusSelect: function (e) {
            if (this.clicked === false) {
                return;
            }
            if (this.action === 'search') {
                Backbone.trigger('searchForBus', e.target.value);
                this.hlBus = e.target.value;
            } else if (this.action === 'assign') {
                if (!this.selected) {
                    return;
                }
                let route = this.model.findWhere({route_name: e.target.value}).attributes;
                route.space = this.selected.id;
                route.status = 'a';
                bus.sendUpdate(route);
            }

            this.handleReturnClick();
        },
        handleReturnClick: function (e) {
            if (e) {
                e.stopPropagation();
            }
            this.clicked = false;
            this.render();
        },
        handleAction: function () {
            if (this.clicked) {
                return;
            }
            switch (this.action) {
                case 'search':
                    this.searchBus();
                    break;
                case 'assign':
                    this.assignBus();
                    break;
                case 'unassign':
                    this.unassignBus();
                    break;
                default:
                    break;
            }
        },
        searchBus: function () {
            this.clicked = true;
            if (this.hlBus) {
                Backbone.trigger('deselectBus', this.hlBus);
                this.hlBus = null;
            }
            this.render();
        },
        assignBus: function () {
            this.clicked = true;
            this.render();
        },
        unassignBus: function () {
            let route = $(this.selected).data('route');
            route.status = 'o';
            route.space = '';
            bus.sendUpdate(route);
        },
        handleEmptySpace: function (space) {
            if (!isAdmin) {
                return;
            }
            this.icon = 'fa-plus-square';
            this.text = 'assign bus';
            this.action = 'assign';
            this.selected = space;
            this.render();
        },
        handleFilledSpace: function (space) {
            if (!isAdmin) {
                return;
            }
            this.icon = 'fa-minus-square';
            this.text = 'unassign bus';
            this.action = 'unassign';
            this.selected = space;
            this.render();
        },
        handleDeselectSpace: function () {
            this.icon = 'fa-search';
            this.text = 'search for bus';
            this.action = 'search';
            this.render();
        }
    });

    bus.MapView = Backbone.View.extend({
        initialize: function () {
            _.bindAll(this, 'render');
            this.template = _.template($('#map-view').html());
            this.model = [];
            this.hlRouteNames = [];
            this.selected = null;

            Backbone.on('searchForBus', this.selectBus, this);
            Backbone.on('deselectBus', this.deselectBus, this);
        },

        events: {
            'click path': 'selectSpace',
            'click': 'deselectSpace'
        },

        render: function () {
            var container = this.$el,
                renderedContent = this.template({}),
                hlRouteNames = this.hlRouteNames,
                collection = this.model;
            container.html(renderedContent);
            var draw = SVG.adopt(container.find('svg')[0]);
            collection.forEach(function (route) {
                if (route.attributes.status === 'a' && route.attributes.space) {
                    var space = container.find(`#${route.attributes.space}`)[0];
                    if (space) {
                        let text = draw.text(route.attributes.route_name);
                        text.path(space.getAttribute('d'));
                        text.style('pointer-events', 'none');
                        space.style.fill = '#FFD800';
                        $(space).data({
                            'filled': true,
                            'route': route.attributes
                        });

                        if (hlRouteNames.includes(route.attributes.route_name)) {
                            space.style.fill = '#0048ab';
                            text.fill('white');
                        }
                    }
                }
            });
            return this;
        },

        selectBus: function (routeNumber) {
            this.hlRouteNames.push(routeNumber);
            this.render();
        },

        deselectBus: function (routeNumber) {
            let i = this.hlRouteNames.indexOf(routeNumber);
            if (i === -1) {
                return;
            }
            this.hlRouteNames.splice(i, 1);
            this.render();
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
                Backbone.trigger('selectEmptySpace', space);
            } else {
                Backbone.trigger('selectFilledSpace', space);
            }
            space.style.stroke = 'black';
            this.selected = space;
        },

        deselectSpace: function (e) {
            if (this.selected) {
                this.selected.style.stroke = 'none';
                this.selected = null;
                Backbone.trigger('deselectSpace');
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
            this.showingWidget = false;

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
            container.append(this.mapView.render().el);

            // let statusGroups = this.routeList.groupBy('status');

            // _.each(this.categories, function (cat) {
            //     let statusGroup = new bus.StatusGroupModel({
            //         name: window.label_status_strings[cat].name,
            //         empty_text: window.label_status_strings[cat].empty_text,
            //         collection: statusGroups[cat] || []
            //     });
            //     container.append(new bus.StatusGroupView({model: statusGroup }).render().el);
            // });

            // container.append(renderedContent);
            return this;
        },

        update: function (data) {
            if (data.error) {
                Messenger().error(data.error);
                return;
            }
            this.routeList.reset(data.allRoutes);
            this.actionButtonView.model = this.routeList;
            this.mapView.model = this.routeList;

            this.user_bus = this.routeList.find((route) => {
                if (data.userRouteId) {
                    return route.id === data.userRouteId;
                } else if (this.user_bus) {
                    return route.id === this.user_bus.id;
                }
            });


            this.user_bus = this.user_bus ? this.user_bus : new bus.Route();
            this.personalStatusView.model = this.user_bus;


            // FIXME: hacky solution to reset action button.
            Backbone.trigger('deselectSpace');
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
        console.log('Disconnected');
        let msg = Messenger().error({
            message: 'Connection Lost',
            hideAfter: 0,
            showCloseButton: false
        });
        disconnected = msg;
    };

    // window.personalStatusView = new bus.personalStatusView();
});

