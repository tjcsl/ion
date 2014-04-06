from django.db import models

class Time(models.Model):
    hour = models.IntegerField()
    min = models.IntegerField()

    def __unicode__(self):
        return "{}:{}".format(self.hour, self.min)

class Block(models.Model):
    period = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    start = models.ForeignKey('Time', related_name='blockstart')
    end = models.ForeignKey('Time', related_name='blockend')

    def __unicode__(self):
        return "{}: {} ({}-{})".format(self.period, self.name, self.start, self.end)

class CodeName(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

class DayType(models.Model):
    name = models.CharField(max_length=100)
    codenames = models.ManyToManyField('CodeName', blank=True)
    special = models.BooleanField(default=False)
    blocks = models.ManyToManyField('Block', blank=True)

    def __unicode__(self):
        return self.name

class Day(models.Model):
    date = models.DateField()
    type = models.ForeignKey('DayType')

    def __unicode__(self):
        return "{}: {}".format(unicode(self.date), self.type)
