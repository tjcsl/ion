$(document).ready(function() {
    // TODO: Move the logic from jQuery to separate functions,
    // e.g. announcements.delete(id)

    $(".announcement-delete").click(function() {
        var announcement_id = $(this).attr("data-id"),
            announcement_title = $(".announcement[data-id=" + announcement_id + "] > h3")[0].textContent.trim();

        if(!confirm("Delete announcement \"" + announcement_title + "\"?")) return;

        $.post("/announcements/delete", {"id": announcement_id})
            .done(function(data) {
                $(".announcement[data-id=" + announcement_id + "]").slideUp();
                Messenger().success("Successfully deleted announcement.");
            })
            .fail;(function(data) {
                Messenger().error("Error deleting announcement.");
        });
    });

    $('div[data-placeholder]').on('keydown keypress input', function() {
        if(this.textContent) {
            this.dataset.divPlaceholderContent = 'true';
        } else {
            delete(this.dataset.divPlaceholderContent);
        }
    });
});
