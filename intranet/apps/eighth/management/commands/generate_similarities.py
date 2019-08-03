import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from intranet.apps.eighth.models import EighthActivity, EighthActivitySimilarity


class Command(BaseCommand):
    help = "Generate similarities for all activities"

    def add_arguments(self, parser):
        parser.add_argument("--run", action="store_true", dest="run", default=False, help="Run.")

    def handle(self, *args, **options):
        print(EighthActivitySimilarity.objects.all().delete())
        start = time.time()
        acts = (
            EighthActivity.objects.all()
            .exclude(restricted=True)
            .exclude(special=True)
            .exclude(administrative=True)
            .exclude(deleted=True)
            .order_by("name")
        )
        for act in acts:
            start_act = time.time()
            freq_users = act.frequent_users
            for u_info in freq_users:
                u_id = u_info["eighthsignup_set__user"]
                for act_info in get_user_model().objects.get(id=u_id).frequent_signups.exclude(scheduled_activity__activity=act):
                    act_id = act_info["scheduled_activity__activity"]
                    act2 = EighthActivity.undeleted_objects.get(id=act_id)
                    if EighthActivitySimilarity.objects.filter(activity_set__id=act.id).filter(activity_set__id=act2.id).exists():
                        sim = EighthActivitySimilarity.objects.filter(activity_set__id=act.id).filter(activity_set__id=act2.id).first()
                        sim.count += 1
                    else:
                        sim = EighthActivitySimilarity.objects.create(count=0, weighted=0)
                        sim.activity_set.add(act, act2)
                        sim.count = 1
                    sim.save()
            print("Finished similarities for {} in {} seconds".format(act, time.time() - start_act))
        for act in acts:
            if act.is_popular:
                for sim in act.similarities.all():
                    sim.count *= 2
                    sim.save()
        for sim in EighthActivitySimilarity.objects.all():
            sim.update_weighted()
        print("Generated similarities in {} seconds".format(time.time() - start))
