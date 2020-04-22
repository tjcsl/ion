from django.conf import settings
from django.db import models

from ...utils.date import get_senior_graduation_year


class College(models.Model):
    name = models.CharField(max_length=1000)
    ceeb = models.IntegerField(unique=True)

    def __str__(self):
        return "{} ({})".format(self.name, self.ceeb)

    class Meta:
        ordering = ["name"]


class SeniorManager(models.Manager):
    def filled(self):
        return Senior.objects.exclude(college=None, major=None).filter(user__graduation_year=get_senior_graduation_year())


class Senior(models.Model):
    objects = SeniorManager()
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    college = models.ForeignKey(College, blank=True, null=True, on_delete=models.CASCADE)
    MAJORS = [
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
        "Mathematics & Computer Science",
    ]
    major = models.CharField(max_length=100, choices=[(i, i) for i in MAJORS] + [("", "Undecided")], blank=True, null=True)
    college_sure = models.BooleanField(default=False)
    major_sure = models.BooleanField(default=False)

    def __str__(self):
        return "{}".format(self.user)

    class Meta:
        ordering = ["user"]
