from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from ....oauth.models import CSLApplication
from ...models import App


class Command(BaseCommand):
    help = "Creates commonly-used CSL apps for development."

    def handle(self, *args, **options):
        APPS = [
            {
                "order": 10,
                "name": "Webmail",
                "description": "Access your TJ email account",
                "url": "https://webmail.tjhsst.edu/",
                "html_icon": "<i class='fas fa-envelope'></i>",
            },
            {
                "order": 20,
                "name": "Director",
                "description": "Web hosting interface",
                "url": "https://director.tjhsst.edu/",
                "oauth_application": CSLApplication.objects.get_or_create(name="Director 4.0", sanctioned=True)[0],
                "auth_url": "https://director.tjhsst.edu/login/ion/",
                "html_icon": "<i class='fas fa-cloud' style='color: #003060; left: 0;'></i>",
            },
            {
                "order": 30,
                "name": "Tin",
                "description": "Autograder for CS classes",
                "url": "https://tin.tjhsst.edu/",
                "oauth_application": CSLApplication.objects.get_or_create(name="Turn-in", sanctioned=True)[0],
                "auth_url": "https://tin.tjhsst.edu/login/ion/",
                "image_url": "/static/img/cslapps/tin.svg",
                "invert_image_color_for_dark_mode": True,
            },
            {
                "order": 40,
                "name": "JupyterHub",
                "description": "Web interface for the TJ Cluster",
                "url": "https://jupyterhub.tjhsst.edu/",
                "oauth_application": CSLApplication.objects.get_or_create(name="JupyterHub", sanctioned=True)[0],
                "auth_url": "https://jupyterhub.tjhsst.edu/hub/oauth_login",
                "image_url": "/static/img/cslapps/jupyterhub.png",
            },
            {
                "order": 50,
                "name": "Mattermost",
                "description": "Collaboration platform",
                "url": "https://matterless.tjhsst.edu/",
                "image_url": "/static/img/cslapps/mattermost.png",
            },
            {
                "order": 60,
                "name": "Mail Forwarding",
                "description": "Forward your TJ email to another address",
                "url": "https://mailforwarding.tjhsst.edu/",
                "oauth_application": CSLApplication.objects.get_or_create(name="CSL Mail Forwarding", sanctioned=True)[0],
                "auth_url": "https://mailforwarding.tjhsst.edu/login/ion/",
                "image_url": "/static/img/cslapps/mailforwarding.png",
                "invert_image_color_for_dark_mode": True,
            },
            {
                "order": 70,
                "name": "Othello",
                "description": "Othello tournament platform for AI classes",
                "url": "https://othello.tjhsst.edu/",
                "oauth_application": CSLApplication.objects.get_or_create(name="Othello", sanctioned=True)[0],
                "auth_url": "https://othello.tjhsst.edu/oauth/login/ion/",
                "image_url": "/static/img/cslapps/othello.png",
            },
            {
                "order": 80,
                "name": "Tiny",
                "description": "URL shortener",
                "url": "https://tiny.tjhsst.edu/",
                "oauth_application": CSLApplication.objects.get_or_create(name="tiny.tjhsst.edu", sanctioned=True)[0],
                "auth_url": "https://tiny.tjhsst.edu/oauth/login/ion/",
                "html_icon": "<i class='fas fa-link'></i>",
            },
            {
                "order": 90,
                "name": "Password",
                "description": "Change your TJ password",
                "url": "https://resetter.tjhsst.edu/",
                "html_icon": "<i class='fas fa-key'></i>",
            },
            {
                "order": 100,
                "name": "Sysadmins",
                "description": "Learn about the Computer Systems Lab and the Student Sysadmins who run it",
                "url": "https://sysadmins.tjhsst.edu/",
                "image_url": "/static/img/csl_logo.png",
            },
            {
                "order": 110,
                "name": "Status",
                "description": "Information on TJ CSL service status",
                "url": "https://status.tjhsst.edu/",
                "image_url": "/static/img/cslapps/status.png",
                "invert_image_color_for_dark_mode": True,
            },
            {
                "order": 120,
                "name": "Guides",
                "description": "Guides for TJ CSL services",
                "url": "https://guides.tjhsst.edu/",
                "html_icon": "<i class='fas fa-book'></i>",
            },
            {
                "order": 1000,
                "name": "Documentation",
                "description": "Documentation for TJ CSL services",
                "url": "https://documentation.tjhsst.edu/",
                "html_icon": "<i class='fas fa-book'></i>",
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
            {
                "order": 1010,
                "name": "CSL Mattermost",
                "description": "Internal CSL communication",
                "url": "https://mattermost.tjhsst.edu/",
                "image_url": "/static/img/cslapps/mattermost.png",
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
            {
                "order": 1020,
                "name": "Slack",
                "description": "CSL Slack workspace",
                "url": "https://tjcsl.slack.com/",
                "image_url": "/static/img/cslapps/slack.png",
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
            {
                "order": 1030,
                "name": "GitLab",
                "description": "CSL repositories",
                "url": "https://gitlab.tjhsst.edu/",
                "image_url": "/static/img/cslapps/gitlab.png",
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
            {
                "order": 1040,
                "name": "Runbooks",
                "description": "Internal documentation",
                "url": "https://runbooks.tjhsst.edu/",
                "oauth_application": CSLApplication.objects.get_or_create(name="CSL Runbooks", sanctioned=True)[0],
                "auth_url": "https://runbooks.tjhsst.edu/auth",
                "image_url": "/static/img/csl_logo.png",
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
            {
                "order": 1050,
                "name": "GitBook",
                "description": "Edit documentation",
                "url": "https://tjcsl.gitbook.io/",
                "image_url": "/static/img/cslapps/gitbook.png",
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
            {
                "order": 1060,
                "name": "Grafana",
                "description": "Monitoring dashboard",
                "url": "https://grafana.tjhsst.edu/",
                "image_url": "/static/img/cslapps/grafana.png",
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
            {
                "order": 1070,
                "name": "LibreNMS",
                "description": "Network monitoring",
                "url": "https://nms.tjhsst.edu/",
                "image_url": "/static/img/cslapps/librenms.png",
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
            {
                "order": 1080,
                "name": "Better Uptime",
                "description": "Status page dashboard",
                "url": "https://betteruptime.com/team/58077/monitors",
                "image_url": "/static/img/cslapps/betteruptime.svg",
                "invert_image_color_for_dark_mode": True,
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
            {
                "order": 1090,
                "name": "Kibana",
                "description": "Elastic stack and log viewer",
                "url": "https://kibana.tjhsst.edu/",
                "image_url": "/static/img/cslapps/kibana.png",
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
            {
                "order": 1100,
                "name": "Netbox",
                "description": "Infrastructure management",
                "url": "https://netbox.tjhsst.edu/",
                "image_url": "/static/img/cslapps/netbox.png",
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
            {
                "order": 1120,
                "name": "Notes",
                "description": "Internal notes site",
                "url": "https://notes.tjhsst.edu/",
                "auth_url": "https://notes.tjhsst.edu/auth/gitlab",
                "html_icon": "<i class='fas fa-file-alt'></i>",
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
            {
                "order": 1130,
                "name": "Workstatus",
                "description": "Workstations status",
                "url": "https://workstatus.tjhsst.edu/",
                "oauth_application": CSLApplication.objects.get_or_create(name="Workstatus", sanctioned=True)[0],
                "auth_url": "https://workstatus.tjhsst.edu/login/ion/",
                "html_icon": "<i class='fas fa-desktop'></i>",
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
            {
                "order": 1140,
                "name": "Signage",
                "description": "Signage management",
                "url": "https://signage.tjhsst.edu/admin",
                "oauth_application": CSLApplication.objects.get_or_create(name="Signage", sanctioned=True)[0],
                "auth_url": "https://signage.tjhsst.edu/login/ion/",
                "html_icon": "<i class='fas fa-sign'></i>",
                "groups": [Group.objects.get_or_create(name="Sysadmin(R) -- Permissions")[0]],
            },
        ]

        for app in APPS:
            if App.objects.filter(url=app["url"]).count() == 0:
                if "groups" in app:
                    groups = app.pop("groups")
                    new_app = App.objects.create(**app)
                    new_app.groups_visible.set(groups)
                else:
                    App.objects.create(**app)
                self.stdout.write(self.style.SUCCESS(f"Created app {app['name']}"))
            else:
                self.stdout.write(self.style.WARNING(f"App {app['name']} already exists. Updating with new configuration."))
                if "groups" in app:
                    groups = app.pop("groups")
                    new_app = App.objects.filter(url=app["url"])
                    new_app.update(**app)
                    new_app[0].groups_visible.set(groups)
                else:
                    App.objects.filter(url=app["url"]).update(**app)
        self.stdout.write(self.style.SUCCESS("Finished creating apps."))
