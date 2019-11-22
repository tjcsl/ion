/* globals Messenger */
var bus = {};

$(function() {
    let base_url = window.location.host;

    bus.sendUpdate = function (data) {
        //console.log('Sending data:', data);
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
        className: 'action-view bordered-element',
        initialize: function () {
            _.bindAll(this, 'render');
            this.buttonTemplate = _.template($('#action-button-view').html());
            this.searchTemplate = _.template($('#search-widget-view').html());
            this.model = [];
            this.busDriver = false;
            if (!window.isAdmin) {
                console.log('Not admin');
            } else {
                console.log('Admin');
            }
            if (!window.isAdmin) {
                this.icon = 'fas fa-search';
                this.text = 'search for bus';
                this.action = 'search';
            } else {
                this.icon = 'fas fa-check-square';
                this.text = 'mark bus arrived';
                this.action = 'arrive';
            }

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
                                   .filter(bus => bus.attributes.route_name.includes('JT'))
                                   .map(bus => bus.attributes);
            } else if (action === 'arrive') {
                busList = routeList.filter(bus => !bus.attributes.route_name.includes('JT'))
                                   .map(bus => {
                                       if (bus.attributes.status === 'a') {
                                           // TODO: less hacky deep copy
                                           let attr = JSON.parse(JSON.stringify(bus.attributes));
                                           attr.route_name = `Mark ${bus.attributes.route_name} on time`;
                                           return attr;
                                       } else {
                                           return bus.attributes;
                                       }
                                   });
            } else if (action === 'assign') {
                busList = routeList.filter(bus => bus.attributes.status !== 'a')
                                   .map(bus => bus.attributes);
            }
            container.find('select').selectize({
                'options': busList,
                'valueField': 'route_name',
                'labelField': 'route_name',
                'placeholder': action,
                'searchField': 'route_name',
                'sortField': [
                    {
                        field: 'route_name',
                        direction: 'asc'
                    },
                    {
                        field: '$score'
                    }
                ]
            })[0].selectize.focus();
            return this;
        },
        handleBusSelect: function (e) {
            if (this.clicked === false) {
                return;
            }
            if (!isAdmin && this.busDriver) {
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
            } else if (this.action === 'arrive') {
                let route_name = '';
                let st = '';
                // TODO: this is also super hacky
                // Essentially, this checks if the selected route has "Mark"
                // at the beginning, implying that it's to be marked on time.
                if (e.target.value.indexOf('Mark') === 0) {
                    route_name = e.target.value.split(' ')[1];
                    st = 'o';
                } else {
                    route_name = e.target.value;
                    st = 'a';
                }
                console.log(bus);
                let route = this.model.findWhere({route_name: route_name}).attributes;
                route.status = st;
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
                case 'arrive':
                    this.arriveBus();
                    break;
                case 'vroom':
                    if (enableBusDriver) {
                        this.vroom();
                        break;
                    }
                case 'stop-bus':
                    window.location = window.location;
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
        arriveBus: function () {
            this.clicked = true;
            this.render();
        },
        vroom: function () {
            this.busDriver = true;
            this.icon = 'fas fa-arrow-left';
            this.text = 'run out of gas?';
            this.action = 'stop-bus';
            Messenger().post('Use the arrow keys or WASD to drive!');
            this.render();
            Backbone.trigger('vroom-vroom', this.selected);
        },
        handleEmptySpace: function (space) {
            if (!isAdmin && enableBusDriver) {
                this.icon = 'fas fa-bus';
                this.text = 'skrt skrt';
                this.action = 'vroom';
                this.selected = space;
                return this.render();
            }
            this.icon = 'fas fa-plus-square';
            this.text = 'assign bus';
            this.action = 'assign';
            this.selected = space;
            return this.render();
        },
        handleFilledSpace: function (space) {
            if (!isAdmin && enableBusDriver) {
                this.icon = 'fas fa-bus';
                this.text = 'skrt skrt';
                this.action = 'vroom';
                this.selected = space;
                return this.render();
            }
            this.icon = 'fas fa-minus-square';
            this.text = 'unassign bus';
            this.action = 'unassign';
            this.selected = space;
            this.render();
        },
        handleDeselectSpace: function () {
            if (this.busDriver) {
                this.icon = 'fas fa-arrow-left';
                this.text = 'ran out of gas?';
                this.action = 'stop-bus';
                this.render();
                return;
            }
            if (!window.isAdmin) {
                this.icon = 'fas fa-search';
                this.text = 'search for bus';
                this.action = 'search';
            } else {
                this.icon = 'fas fa-check-square';
                this.text = 'mark bus arrived';
                this.action = 'arrive';
            }
            this.render();
        }
    });

    bus.MapView = Backbone.View.extend({
        initialize: function () {
            _.bindAll(this, 'render');
            this.template = _.template($('#map-view').html());
            this.userRoute = null;
            this.model = [];
            this.hlRouteNames = [];
            this.selected = null;

            // vroom vroom
            this.busDriver = false;
            this.busDriverBus = null;
            this.mapbox = null;

            Backbone.on('searchForBus', this.selectBus, this);
            Backbone.on('deselectBus', this.deselectBus, this);
            Backbone.on('driveBus', this.driveBus, this);
            Backbone.on('slowBus', this.slowBus, this);
            if (enableBusDriver) {
                Backbone.on('vroom-vroom', this.vroom, this);
            }
        },

        events: {
            'click path': 'selectSpace',
            'click': 'deselectSpace',
        },

        render: function () {
            if (enableBusDriver && this.busDriver) {

                return this;
            }
            var container = this.$el,
                renderedContent = this.template({}),
                hlRouteNames = this.hlRouteNames,
                userRoute = this.userRoute,
                collection = this.model;
            container.html(renderedContent);
            var draw = SVG.adopt(container.find('svg')[0]);
            collection.forEach(function (route) {
                if (route.attributes.status === 'a' && route.attributes.space) {
                    var space = container.find(`#${route.attributes.space}`)[0];
                    if (space) {
                        let text = draw.text(route.attributes.route_name);
                        text.path(space.getAttribute('d'));
                        text.textPath().attr("path", space.getAttribute('d'));
                        text.style('pointer-events', 'none');
                        // Signage displays may not have Helvetica or Arial installed, so we provide some sane
                        // fallbacks to avoid issues that have appeared in the past with the "sans-serif" default.
                        text.font("family", "Helvetica, Arial, 'Open Sans', 'Liberation Sans', sans-serif");

                        if(window.isSignage) {
                            var tspan = $(text.node).find("tspan");
                            tspan.attr({"x": 0, "dy": 20.5});

                            // If we run this directly, it hasn't rendered yet, so we have to run it after a timeout
                            setTimeout(function() {
                                var tbox = tspan.get(0).getBBox();
                                var sbox = space.getBBox();

                                var offset;
                                var dimenDiff;
                                if(tbox.width > tbox.height) {
                                    dimenDiff = sbox.width - tbox.width;
                                    offset = tbox.x - sbox.x;
                                }
                                else {
                                    dimenDiff = sbox.height - tbox.height;
                                    offset = tbox.y - sbox.y;
                                }

                                if(dimenDiff < offset + 5) {
                                    text.node.classList.add("small");
                                    if(route.attributes.route_name.length > 5) {
                                        text.node.classList.add("extra-small");
                                    }
                                }
                            }, 0);
                        }
                        else {
                            var tspan = $(text.node).find("tspan");

                            setTimeout(function() {
                                var tbox = tspan.get(0).getBBox();
                                var sbox = space.getBBox();

                                var offset;
                                var dimenDiff;
                                if(tbox.width > tbox.height) {
                                    dimenDiff = sbox.width - tbox.width;
                                    offset = tbox.x - sbox.x;
                                }
                                else {
                                    dimenDiff = sbox.height - tbox.height;
                                    offset = tbox.y - sbox.y;
                                }
                                if(dimenDiff < offset + 5 || route.attributes.route_name.length > 5) {
                                    text.node.classList.add("extra-small");
                                }
                            }, 0);
                        }
                        space.style.fill = '#FFD800';
                        $(space).data({
                            'filled': true,
                            'route': route.attributes
                        });

                        if (hlRouteNames.includes(route.attributes.route_name)) {
                            space.style.fill = '#0048ab';
                            text.fill('white');
                        }

                        if (route.attributes.route_name === userRoute && hlRouteNames.length === 0) {
                            space.style.fill = '#e00000';
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

        deselectSpace: function () {
            if (this.selected) {
                this.selected.style.stroke = 'none';
                this.selected = null;
                Backbone.trigger('deselectSpace');
            }
        },

        highlightUserBus: function (bus) {
            if (!this.userRoute) {
                this.userRoute = bus.route_name;
            }
        },

        vroom: function () {
            // Initializes busdriver
            //console.log('Hi');
            if (enableBusDriver) {
                this.busDriver = true;
                $('svg').hide();
                mapboxgl.accessToken = 'pk.eyJ1IjoibmFpdGlhbnoiLCJhIjoiY2pmY3p0cWQwMzZncjJ5bXpidDAybGw2aCJ9.-cGh2TszqtE9hxum3qM9Dw';
                this.mapbox = new mapboxgl.Map({
                    container: 'map',
                    style: 'mapbox://styles/mapbox/satellite-v9',
                    zoom: 18.5,
                    bearing: -49,
                    center: [-77.16772, 38.81932]
                });
                this.mapbox.keyboard.disable();
                this.mapbox.dragPan.disable();
                this.mapbox.scrollZoom.disable();
                this.mapbox.on('load', function () {
                    // Callback hell, my old friend.
                    this.busDriverBus = {
                        'speed': 0, // km/hr
                        'direction': Math.PI / 16, // radians
                        'acceleration': 0,
                        'point': {
                            'type': 'Point',
                            'coordinates': [-77.16772, 38.81932]
                        },
                        'lastFrame': null,
                        'elapsedTime': 0,
                        'pressed': false
                    };
                    this.busDriverEl = $('.busdriver-bus#bd-bus');
                    this.busDriverEl.addClass('vroom');
                    requestAnimationFrame(this.animateBus.bind(this));
                }.bind(this));
                // this.render();
            }
        },

        driveBus: function (e) {
            if (!this.busDriverBus) {
                return;
            }
            if (e.keyCode === 37 || e.keyCode === 65) {
                this.busDriverBus.direction -= this.busDriverBus.speed * Math.PI / 180;
                this.busDriverBus.pressed = true;
            }
            if (e.keyCode === 39 || e.keyCode === 68) {
                this.busDriverBus.direction += this.busDriverBus.speed * Math.PI / 180;
                this.busDriverBus.pressed = true;
            }
            if (e.keyCode === 38 || e.keyCode === 87) {
                this.busDriverBus.speed = Math.min(this.busDriverBus.speed + 1, 10);
                this.busDriverBus.pressed = true;
            }
            if (e.keyCode === 40 || e.keyCode === 83) {
                this.busDriverBus.speed = Math.max(this.busDriverBus.speed - 1, 0);
            }
        },

        slowBus: function (e) {
            if (!this.busDriverBus) {
                return;
            }
            if (e.keyCode === 38 || e.keyCode === 87) {
                this.busDriverBus.pressed = false;
            }
        },

        animateBus: function (time) {
            if (document.hidden || time - this.busDriver.lastFrame > 2000) {
                console.log('hidden');
                this.busDriverBus.lastFrame = time;
                return;
            }
            if (enableBusDriver) {
                if (!this.busDriverBus.lastFrame) {
                    this.busDriverBus.lastFrame = time;
                }
                // t should be ms
                let t = (time - this.busDriverBus.lastFrame) / 1000; // Hack...
                if (!this.busDriverBus.pressed) {
                    this.busDriverBus.speed *= 0.993;
                }
                let speed = this.busDriverBus.speed;
                let direction = this.busDriverBus.direction;
                let point = this.busDriverBus.point;

                // km/hr * hr/60min * min/60s * s/1000ms = km/ms
                // mapbox does angles where pointing up is 0˚ and it increases clockwise
                // equatorial radius of Earth = 6,378.1370 km
                // polar radius of Earth = 6,356.7523 km

                 // length of 1 deg equatorial longitude
                let deg_lng_eq = 6378.1370 * 2 * Math.PI / 360;
                // length of 1 deg equatorial latitude
                let deg_lat_eq = 6356.7523 * 2 * Math.PI / 360;

                let x = speed * t * Math.sin(direction) / (60 * 60 * 1000);
                let y = speed * t * Math.cos(direction) / (60 * 60 * 1000);
                let old_lat = point.coordinates[1];
                let old_lng = point.coordinates[0];
                let rad_lat = old_lat * Math.PI / 180;
                point.coordinates[0] += deg_lng_eq * Math.cos(rad_lat) * x; // longitude
                point.coordinates[1] += deg_lat_eq * y; // latitude
                /*if (Math.abs(x) !== 0 && Math.abs(y) !== 0) {
                    console.log('------------------------------------');
                    console.log('∆x', x);
                    console.log('∆y', y);
                    console.log('∆t', t);
                    console.log('∆lng', 111.320 * Math.cos(rad_lat) * x);
                    console.log('∆lat', 110.574 * y);
                    console.log('oldlat', old_lat);
                    console.log('oldlng', old_lng);
                    console.log('newlat', point.coordinates[1]);
                    console.log('newlng', point.coordinates[0]);
                    console.log('bdb', this.busDriverBus);
                }*/
                let degrees = (direction) * (180 / Math.PI) - 49 + 90;
                // let degrees = (direction) * (180 / Math.PI);
                this.busDriverEl.css({'transform' : 'rotate('+ degrees +'deg)'});
                this.mapbox.setCenter(this.busDriverBus.point.coordinates);

                this.busDriverBus.lastFrame = time;
                this.busDriverBus.elapsedTime += t;
                window.requestAnimationFrame(this.animateBus.bind(this));
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
            container.children().detach();
            if (!window.isAdmin || window.isStudent) {
                container.append(this.personalStatusView.render().el);
            }
            container.append(this.actionButtonView.render().el);
            container.append(this.mapView.render().el);

            return this;
        },

        update: function (data) {
            if (data.error) {
                Messenger().error(data.error);
                return;
            }
            if (this.mapView.busDriver) {
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

            this.mapView.highlightUserBus(this.user_bus.attributes);

            // FIXME: hacky solution to reset action button.
            Backbone.trigger('deselectSpace');
            this.render();
        }
    });

    if (enableBusDriver) {
        $('body').on('keydown', function (e) {
            Backbone.trigger('driveBus', e);
        });
        $('body').on('keyup', function (e) {
            Backbone.trigger('slowBus', e);
        });
    }

    const protocol = (location.protocol.indexOf('s') > -1) ? 'wss' : 'ws';
    if (enableBusDriver) {
        console.log('Bus Driver Enabled');
    }
    let socket;
    if (base_url !== '') {
        socket = new ReconnectingWebSocket(`${protocol}://${base_url}/bus/`);
    } else {
        socket = new ReconnectingWebSocket(`${websocketProtocol}://${websocketHost}/bus/`);
    }
    socket.automaticOpen = true;
    socket.reconnectInterval = 2000;
    socket.maxReconnectInterval = 10000;
    socket.reconnectDecay = 1.25;
    socket.timeoutInterval = 5000;
    socket.maxReconnectAttempts = null;

    let disconnected = false;
    let disconnected_msg = null;
    window.appView = new bus.AppView();

    socket.onopen = () => {
        if(keepAliveTimeoutId != null) {
            clearTimeout(keepAliveTimeoutId);
            keepAliveTimeoutId = null;
        }

        if (disconnected_msg) {
            disconnected_msg.update({
                message: 'Connection Restored',
                type: 'success',
                hideAfter: 3
            });
        }
    };

    let keepAliveTimeoutId = null;

    socket.onmessage = (event) => {
        if(keepAliveTimeoutId != null) {
            clearTimeout(keepAliveTimeoutId);
            keepAliveTimeoutId = null;
        }

        var data = JSON.parse(event.data)

        // Don't try and handle keepalives -- when handled, they effectively clear the bus board
        if(data.type === "keepalive-response") {
            return;
        }

        window.appView.trigger('wss:receive', data);
    };

    socket.onclose = () => {
        console.log('Disconnected');
        if(window.Messenger) {
            disconnected_msg = Messenger().error({
                message: 'Connection Lost',
                hideAfter: 0,
                showCloseButton: false
            });
        }
        disconnected = true;

        if(keepAliveTimeoutId != null) {
            clearTimeout(keepAliveTimeoutId);
            keepAliveTimeoutId = null;
        }
    };

    setInterval(function() {
        if(!disconnected) {
            socket.send(JSON.stringify({"type": "keepalive"}));

            keepAliveTimeoutId = setTimeout(function() {
                if(!disconnected) {
                    socket.refresh();
                }
            }, 10000);
        }
    }, 30000);

    if (enableBusDriver) {
        $(window).unload(function () {
            alert('hello');
            alert(`You drove ${window.appView.mapView.busDriverBus.elapsedTime} milliseconds!`);
            Backbone.trigger('recordScore', e);
        });
    }
// window.personalStatusView = new bus.personalStatusView();
});
