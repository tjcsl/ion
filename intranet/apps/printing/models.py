from django.conf import settings
from django.db import models


class PrintJob(models.Model):
    """ Represents a submitted print job to Ion printing.

    Attributes:
        user (:obj:`User`): The user submitting the job.
        printer (str): The printer to run the job on.
        file (File): The file that the user submitted.
        page_range (str): The page range to print.
        time (:obj:`datetime.datetime`): The time the job
            was submitted.
        printed (bool): Whether the job was printed.
        num_pages (int): The number of pages in this job.
            This is calculated after converting the job.
        duplex (bool): Whether to print duplex.
        fit (bool): Whether to fit to page.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    printer = models.CharField(max_length=100)
    file = models.FileField(upload_to="printing/")
    page_range = models.CharField(blank=True, max_length=100)
    time = models.DateTimeField(auto_now_add=True)
    printed = models.BooleanField(default=False)
    num_pages = models.IntegerField(default=0)
    duplex = models.BooleanField(default=True)
    fit = models.BooleanField(default=False, verbose_name="Fit-to-page")

    def __str__(self):
        return "{} by {} to {}".format(self.file, self.user, self.printer)
