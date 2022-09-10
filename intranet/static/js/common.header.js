/* global $ */
$(function() {
    Messenger.options = {
        extraClasses: "messenger-fixed messenger-on-bottom messenger-on-right",
        theme: "flat",
        messageDefaults: {
            hideAfter: 10,
            showCloseButton: true
        }
    };
});

$(function() {
    var time = 150;

    var clickInside = function(event) {
        event.stopPropagation();
    }

    var clickOutside = function(e) {
        if ($(e.target).parents().andSelf().hasClass("dropdown-allow")) return;

        if (!$(e.target).parents().andSelf().hasClass("dropdown-item-wrapper")) {
            closeMenu($(".dropdown-open .dropdown-menu"), true);
            $(".has-dropdown").removeClass("dropdown-open");
        }
    }

    var openMenu = function(menu, bindEvents) {
        menu.show();
        menu.stop().animate({
            top: "0",
            opacity: 1
        }, time, "easeInQuart", function() {
            if (bindEvents) {
                $(document).bind("click tap", clickOutside);
                $(".dropdown-menu").bind("click", clickInside);
            }
        });
    }

    var closeMenu = function(menu, unbindEvents) {
        menu.stop().animate({
            top: "10px",
            opacity: 0
        }, time, "easeOutQuart", function() {
            menu.hide();

            if (unbindEvents) {
                $(".dropdown-menu").unbind("click", clickInside);
                $(document).unbind("click tap", clickOutside);
            }
        });
    }

    $(".has-dropdown").click(function(event) {
        var menu_clicked = $(this).children(".dropdown-menu");
        var already_open = $(".dropdown-open .dropdown-menu")
        var clicked_subgroups = menu_clicked.children(".has-dropdown-subgroup");

        if ($(this).hasClass("dropdown-open")) {
            // Closing open menu and any open subgroups
            closeMenu(menu_clicked);
            clicked_subgroups.children(".dropdown-subgroup").hide();
            clicked_subgroups.children("a.subgroup-arrow-parent").children("i.subgroup-arrow").addClass("fa-caret-down");
            clicked_subgroups.children("a.subgroup-arrow-parent").children("i.subgroup-arrow").removeClass("fa-caret-left");

            $(document).unbind("click tap", clickOutside);
            $(".dropdown-menu").unbind("click", clickInside);
            $(".has-dropdown").removeClass("dropdown-open");
        } else if (already_open.length === 0) {
            // All menus closed, opening one of them
            openMenu(menu_clicked, true);
            menu_clicked.parent().addClass("dropdown-open");
        } else {
            // Switching menu
            openMenu(menu_clicked, false);
            closeMenu(already_open, false);
            $(".has-dropdown").removeClass("dropdown-open");
            menu_clicked.parent().addClass("dropdown-open");
        }
    });

    $(".has-dropdown-subgroup").click(function(event) {
        var subgroup = $(this).children(".dropdown-subgroup");
        var arrow = $(this).children("a.subgroup-arrow-parent").children("i.subgroup-arrow");
        subgroup.toggle();
        arrow.toggleClass("fa-caret-down");
        arrow.toggleClass("fa-caret-left");
    });

    arrowPosition = function() {
        // Calculate dimensions to align arrow to icons/text in header
        $(".notifications .dropdown-menu .arrow").css("right", ($(".notifications").width() / 2) + "px");
        $(".username .dropdown-menu .arrow, .csl-apps .dropdown-menu .arrow").css("right", ((($(".username .dropdown-item-wrapper").width()) / 2) + 5) + "px");
    }

    arrowPosition();
    window.onresize = arrowPosition;
});