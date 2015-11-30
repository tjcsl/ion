# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from random import shuffle
from django.contrib.auth.models import Group as DjangoGroup
from django.utils.html import strip_tags
from django.db import models
from django.db.models import Manager, Q
from django.utils import timezone
from ..users.models import User


class College(models.Model):
    name = models.CharField(max_length=1000)
    ceeb = models.IntegerField(unique=True)

    def __unicode__(self):
        return "{}: {}".format(self.ceeb, self.name)

    class Meta:
        ordering = ["name"]

class Major(models.Model):
    MAJORS = [(i, i) for i in (
        "Computer Science",
        "Engineering",
        "Education",
        "Mathematics",
        "Physics",
        "Biology",
        "Chemistry",
        "Geology",
        "History",
        "Literature",
        "English",
        "Other",
        "Language",
        "Drama/Theater",
        "Undecided",
        "Music",
        "Political Science",
        "Neuroscience",
        "Business",
        "Economics",
        "Communications",
        "World Studies",
        "Art/Art History",
        "Biochemistry",
        "Computer Engineering",
        "Anthropology",
        "Film",
        "Atmospheric Science",
        "Astronomy",
        "Psychology",
        "Genetics",
        "Social Work",
        "Architecture",
        "Public Policy",
        "Classics",
        "Marine Biology",
        "Dance",
        "Philosophy",
        "Emergency Health Services",
        "Animal Science",
        "Computer and Video Imaging",
        "Geography",
        "International Relations",
        "Foreign Service",
        "Broadcast Journalism",
        "Semitic Studies",
        "Microbiology",
        "Finance",
        "Journalism",
        "Aeronautics/Astronautics",
        "Pre-med",
        "Pre-law",
        "Automotive Technician",
        "Computer Game Design",
        "Petroleum Engineering",
        "American Studies",
        "African-American Studies",
        "Linguistics",
        "Sociology",
        "International Finance",
        "Public Policy in Science and Technology",
        "Information Technology",
        "Network Engineering",
        "Environmental Science",
        "Evolutionary Biology",
        "Advertising",
        "Apparel Design",
        "East Asian Studies",
        "Biomedical Engineering",
        "Policy Analysis and Management",
        "Videogame Design and Development",
        "Electrical Engineering",
        "Information Systems",
        "Theatre",
        "Theatre/Directing",
        "Leadership",
        "Design",
        "Environmental Thought and Practice",
        "Athletic Training",
        "Physical Therapy",
        "Chemical Engineering",
        "Athletic Training & Physical Therapy",
        "Civil Engineering",
        "Industrial and Labor Relations",
        "Bowling Management",
        "Pre-Dental",
        "Aerospace Engineering",
        "French",
        "German",
        "Spanish",
        "Italian",
        "Chinese",
        "Operations Research",
        "Game Design and Development",
        "Software Engineering",
        "International Development",
        "Mechanical Engineering",
        "Mathematics & Computer Science"
    )]
    name = models.CharField(max_length=1000, choices=MAJORS)

    def __unicode__(self):
        return "{}".format(self.name)

    class Meta:
        ordering = ["name"]

class Senior(models.Model):
    user = models.OneToOneField(User)
    college = models.ForeignKey(College, blank=False)
    major = models.ForeignKey(Major, blank=False)
    college_sure = models.BooleanField(default=False)
    major_sure = models.BooleanField(default=False)

    def __unicode__(self):
        return "{}".format(self.user)