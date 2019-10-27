from django.urls import reverse

from ...test.ion_test import IonTestCase
from .models import Group


class GroupsTest(IonTestCase):
    def test_groups_view(self):
        admin_all_group = Group.objects.get_or_create(name="admin_all")[0]
        admin_groups_group = Group.objects.get_or_create(name="admin_groups")[0]

        self.client.logout()

        response = self.client.get(reverse("groups"))
        self.assertEqual(response.status_code, 302)

        user = self.login()
        user.groups.clear()

        response = self.client.get(reverse("groups"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["group_admin"], False)
        self.assertQuerysetEqual(response.context["all_groups"], list(map(repr, Group.objects.all())), ordered=False)

        user.groups.set([admin_all_group])
        response = self.client.get(reverse("groups"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["group_admin"], True)
        self.assertQuerysetEqual(response.context["all_groups"], list(map(repr, Group.objects.all())), ordered=False)

        user.groups.set([admin_groups_group])
        response = self.client.get(reverse("groups"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["group_admin"], True)
        self.assertQuerysetEqual(response.context["all_groups"], list(map(repr, Group.objects.all())), ordered=False)

    def test_add_group_view(self):
        admin_all_group = Group.objects.get_or_create(name="admin_all")[0]
        admin_groups_group = Group.objects.get_or_create(name="admin_groups")[0]

        self.client.logout()

        response = self.client.get(reverse("add_groups"))
        self.assertEqual(response.status_code, 302)

        user = self.login()
        user.groups.clear()

        response = self.client.get(reverse("add_groups"))
        self.assertEqual(response.status_code, 302)

        user.groups.set([admin_all_group])
        response = self.client.get(reverse("add_groups"))
        self.assertEqual(response.status_code, 200)

        user.groups.set([admin_groups_group])
        response = self.client.get(reverse("add_groups"))
        self.assertEqual(response.status_code, 200)

        Group.objects.filter(name="test").delete()
        self.assertFalse(Group.objects.filter(name="test").exists())
        response = self.client.post(reverse("add_groups"), {"name": "test", "permissions": []})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Group.objects.filter(name="test").exists())
