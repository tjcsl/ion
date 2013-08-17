from django.forms import ModelForm
from .models import Announcement

class AnnouncementForm(ModelForm):
	class Meta:
		model = Announcement
