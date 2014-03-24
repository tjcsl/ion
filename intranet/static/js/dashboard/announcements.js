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

    $('div[data-placeholder]').on('keydown keypress input', function() {
        if(this.textContent) {
            this.dataset.divPlaceholderContent = 'true';
        } else {
            delete(this.dataset.divPlaceholderContent);
        }
    });
});
