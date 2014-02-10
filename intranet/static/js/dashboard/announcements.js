$(document).ready(function() {

    // TODO: Move the logic from jQuery to separate functions,
    // e.g. announcements.delete(id)

    $(".announcement-delete").click(function() {
        var announcement_id = $(this).attr("data-id"),
            announcement_title = $(".announcement[data-id=" + announcement_id + "] > h3")[0].textContent.trim();

        if(!confirm("Delete announcement \"" + announcement_title + "\"")) return;

        // TODO: Possibly POST to /api
        post("/announcements/delete",
             {"id": announcement_id},
             function(d) {
                $(".announcement[data-id=" + announcement_id + "]").slideUp();
                $(".ajax-message").html("Successfully deleted announcement.")
                                  .click(function() {
                                    $(this).slideUp();
                                  })
                                  .slideDown();
            }
        );
    });

    $(".announcement-add").click(function() {
        /* TODO: Make the add announcement textbox on this same page */
        $('.announcement-add-div').slideDown();
        var today = new Date();
        $('.announcement-add-today').html(
            (['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][today.getDay()]) + ", " +
            (['January','February','March','April','May','June','July','August','September','October','November','December'][today.getMonth()]) + " " +
            today.getDate() + ", " + today.getFullYear()
            );
        $('.announcement-add-title, .announcement-add-content').click(function() {
            /*var h = $(this).html(), p = $(this).attr('placeholder');
            if(trim(h) == trim(p)) {
                $(this).html('');
                this.select();
            } */
        });

        $('.announcement-add-submit').click(function() {
            // .announcement-add-title, .announcement-add-author, .announcement-add-content
            var name = $('.announcement-add-title').html(),
                author = $('.announcement-add-author').html(),
                content = $('.announcement-add-content').html();

            $.post('/announcements/add', {
                'name': name,
                'author': author,
                'content': content
            }, function(d) {
                $('.announcement-add-div').html('Announcement added.');
            });
        })
        // location.href = "/announcements/add";
    });
});

$(function() {
    $('div[data-placeholder]').on('keydown keypress input', function() {
        if(this.textContent) {
            this.dataset.divPlaceholderContent = 'true';
        } else {
            delete(this.dataset.divPlaceholderContent);
        }
    });
});
