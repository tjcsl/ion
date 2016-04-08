# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from ...test.ion_test import IonTestCase

class PreferencesTest(IonTestCase):

    settings_dict = {'showpictures-self': ['on'],
                'mobile_phone': ['5555555555'],
                'showschedule-self': ['on'],
                'home_phone': ['5555555555'],
                'webpage_0': ['https://ion.tjhsst.edu/logout'],
                'receive_push_notifications': ['on'],
                'email_0': ['awilliam@tjhsst.edu'],
                'showbirthday-self': ['on'],
                'preferred_photo': ['AUTO'],
                'other_phone_0': ['5555555555'],
                'showschedule-self': None,
                'showschedule': None,
                'showeighth-self': None,
                'showeighth': None,
                'showschedule': None,
                'showpictures-self': None,
                'showbirthday': None,
                'showpictures': None,
                'showbirthday-self': None,
                'showtelephone-self': None,
                'showtelephone': None,
                'showaddress-self': None,
                'showaddress': None
                }

    def test_get_preferences(self):
        self.login()
        response = self.client.get(reverse('preferences'))
        self.assertEqual(response.status_code, 200)
    
    def test_set_preferences(self):
        self.login()
        response = self.client.post(reverse('preferences'), self.settings_dict)
        self.assertEqual(response.status_code, 200)

    def test_clear_preferences(self):
        self.login()
        self.settings_dict.update({'mobile_phone': '', 'home_phone': '', 'other_phone_0': ''})
        with self.assertLogs("intranet.apps.preferences.views", level="DEBUG") as logger:
            response = self.client.post(reverse('preferences'), self.settings_dict)
        self.assertNotEquals(logger.output, ["DEBUG:intranet.apps.preferences.views:Unable to set field phones with value []: Can not set User attribute 'phones' -- not in user attribute list."])
        self.assertEqual(response.status_code, 200)
