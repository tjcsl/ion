from django.contrib.auth import get_user_model
from django.urls import reverse

from ...test.ion_test import IonTestCase
from .models import FoundItem, LostItem


class LostFoundTestCase(IonTestCase):
    def test_home_view(self):
        response = self.client.get(reverse("lostfound"))
        self.assertEqual(302, response.status_code)  # to login page

        self.login()
        response = self.client.get(reverse("lostfound"))
        self.assertEqual(200, response.status_code)

    def test_lostitem_add_view(self):
        self.login()
        response = self.client.get(reverse("lostitem_add"))
        self.assertEqual(200, response.status_code)

        # Add an item
        response = self.client.post(
            reverse("lostitem_add"), data={"title": "i lost my calculator", "description": "<p>Oh no</p>", "last_seen": "3000-01-01"}, follow=True
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, LostItem.objects.filter(title="i lost my calculator", description="<p>Oh no</p>", last_seen="3000-01-01").count())

    def test_lostitem_modify_view(self):
        self.login()
        user2 = get_user_model().objects.get_or_create(username="awilliam1")[0]
        item = LostItem.objects.create(user=user2, title="hellotest1", description="Hello", last_seen="3000-01-01")

        # Attempts to modify that would result in a 404 because I am not awilliam1
        response = self.client.get(reverse("lostitem_modify", kwargs={"item_id": item.id}))
        self.assertEqual(404, response.status_code)

        # Change the user to awilliam and try again
        user = get_user_model().objects.get(username="awilliam")
        item.user = user
        item.save()
        response = self.client.get(reverse("lostitem_modify", kwargs={"item_id": item.id}))
        self.assertEqual(200, response.status_code)

        # Attempt to modify it
        response = self.client.post(
            reverse("lostitem_modify", kwargs={"item_id": item.id}),
            data={"title": "hellotest2", "description": "Hi there!", "last_seen": "3000-01-01"},
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, LostItem.objects.filter(title="hellotest2", description="Hi there!").count())

    def test_lostitem_delete_view(self):
        self.login()
        user2 = get_user_model().objects.get_or_create(username="awilliam1")[0]
        item = LostItem.objects.create(user=user2, title="hellotest1", description="Hello", last_seen="3000-01-01")

        # Attempts to modify that would result in a 404 because I am not awilliam1
        response = self.client.get(reverse("lostitem_delete", kwargs={"item_id": item.id}))
        self.assertEqual(404, response.status_code)

        # Change the user to awilliam and try again
        user = get_user_model().objects.get(username="awilliam")
        item.user = user
        item.save()
        response = self.client.get(reverse("lostitem_delete", kwargs={"item_id": item.id}))
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse("lostitem_delete", kwargs={"item_id": item.id}), data={"mark_retrieved": True}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, LostItem.objects.filter(title="hellotest1", found=True).count())

        response = self.client.post(reverse("lostitem_delete", kwargs={"item_id": item.id}), data={"full_delete": True}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, LostItem.objects.filter(title="hellotest1").count())

    def test_lostitem_view(self):
        self.login()
        item = LostItem.objects.create(
            user=get_user_model().objects.get(username="awilliam"), title="hellotest1", description="Hello", last_seen="3000-01-01"
        )

        response = self.client.get(reverse("lostitem_view", kwargs={"item_id": item.id}))
        self.assertEqual(200, response.status_code)

    def test_founditem_add_view(self):
        self.login()
        response = self.client.get(reverse("founditem_add"))
        self.assertEqual(200, response.status_code)

        # Add an item
        response = self.client.post(
            reverse("founditem_add"),
            data={"title": "i found this calculator", "description": "<p>Free calculator</p>", "found": "3000-01-01"},
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            1, FoundItem.objects.filter(title="i found this calculator", description="<p>Free calculator</p>", found="3000-01-01").count()
        )

    def test_founditem_modify_view(self):
        self.login()
        user2 = get_user_model().objects.get_or_create(username="awilliam1")[0]
        item = FoundItem.objects.create(user=user2, title="hellotest1", description="Hello", found="3000-01-01")

        # Attempts to modify that would result in a 404 because I am not awilliam1
        response = self.client.get(reverse("founditem_modify", kwargs={"item_id": item.id}))
        self.assertEqual(404, response.status_code)

        # Change the user to awilliam and try again
        user = get_user_model().objects.get(username="awilliam")
        item.user = user
        item.save()
        response = self.client.get(reverse("founditem_modify", kwargs={"item_id": item.id}))
        self.assertEqual(200, response.status_code)

        # Attempt to modify it
        response = self.client.post(
            reverse("founditem_modify", kwargs={"item_id": item.id}),
            data={"title": "hellotest2", "description": "Hi there!", "found": "3000-01-01"},
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, FoundItem.objects.filter(title="hellotest2", description="Hi there!").count())

    def test_founditem_delete_view(self):
        self.login()
        user2 = get_user_model().objects.get_or_create(username="awilliam1")[0]
        item = FoundItem.objects.create(user=user2, title="hellotest1", description="Hello", found="3000-01-01")

        # Attempts to modify that would result in a 404 because I am not awilliam1
        response = self.client.get(reverse("founditem_delete", kwargs={"item_id": item.id}))
        self.assertEqual(404, response.status_code)

        # Change the user to awilliam and try again
        user = get_user_model().objects.get(username="awilliam")
        item.user = user
        item.save()
        response = self.client.get(reverse("founditem_delete", kwargs={"item_id": item.id}))
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse("founditem_delete", kwargs={"item_id": item.id}), data={"mark_retrieved": True}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, FoundItem.objects.filter(title="hellotest1", retrieved=True).count())

        response = self.client.post(reverse("founditem_delete", kwargs={"item_id": item.id}), data={"full_delete": True}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, FoundItem.objects.filter(title="hellotest1").count())

    def test_founditem_view(self):
        self.login()
        item = FoundItem.objects.create(
            user=get_user_model().objects.get(username="awilliam"), title="hellotest1", description="Hello", found="3000-01-01"
        )

        response = self.client.get(reverse("founditem_view", kwargs={"item_id": item.id}))
        self.assertEqual(200, response.status_code)
