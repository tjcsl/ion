# -*- coding: utf-8 -*-

from django.db import models


class Page(models.Model):
    """
        iframe: True if page is just an iframe
        url: url for iframe (if iframe is True)
        sandbox: whether the iframe should be sandboxed
                 https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe#attr-sandbox

        template: the path to the template (for server side rendering)
        button: the name of the fontawesome icon (ex: "fa-chrome")
        order: index at which button should be placed

        strip_links: whether we strip the links in the iframe (to prevent navigation away)

        signs: set of signs which display this Page
    """
    name = models.CharField(max_length=50)

    iframe = models.BooleanField(default=False)
    url = models.URLField(null=True, blank=True)
    sandbox = models.BooleanField(default=True)

    template = models.CharField(max_length=50, null=True, blank=True)
    function = models.CharField(max_length=50, null=True, blank=True)
    button = models.CharField(max_length=140, null=True, blank=True)
    order = models.IntegerField(default=0)

    strip_links = models.BooleanField(default=True)

    def deploy_to(self, displays=None, exclude=[]):
        """
        Deploys page to listed display (specify with display). If display is None,
        deploy to all display. Can specify exclude for which display to exclude.
        This overwrites the first argument.
        """
        if displays is None:
            signs = Sign.objects.all()
        else:
            signs = Sign.objects.filter(display__in=displays)
        for sign in signs.exclude(display__in=exclude):
            sign.pages.add(self)
            sign.save()

    def __str__(self):
        if self.iframe:
            url = self.url[:10]
            url = url + "..." if len(self.url) > 10 else url
            return "{} ({})".format(self.name, url)
        else:
            return "{}".format(self.name)


class Sign(models.Model):
    """
        name: friendly display name [required]
        display: unique name (should match hostname of pi/compute stick) [required]

        eighth_block_increment: ...
        landscape: if display is in landscape orientation
        map_location: location of display on map

        lock_page: if set, the signage will only display this page
        default_page: if set, the signage will revert to this page after a set
                      amount of time
        pages: a list of pages
    """
    name = models.CharField(max_length=1000)
    display = models.CharField(max_length=100, unique=True)
    eighth_block_increment = models.IntegerField(default=0, null=True, blank=True)
    landscape = models.BooleanField(default=False)
    map_location = models.CharField(max_length=20, null=True, blank=True)
    img_path = models.CharField(max_length=100, default="https://c1.staticflickr.com/5/4331/36927945575_c2c09e44db_k.jpg")

    lock_page = models.ForeignKey(Page,
                                  on_delete=models.SET_NULL,
                                  null=True,
                                  blank=True,
                                  related_name="_unused_1")
    default_page = models.ForeignKey(Page,
                                     on_delete=models.SET_NULL,
                                     null=True,
                                     blank=True,
                                     related_name="_unused_2")
    pages = models.ManyToManyField(Page, related_name="signs")

    def __str__(self):
        return "{} ({})".format(self.name, self.display)
