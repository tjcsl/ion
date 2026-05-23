import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from intranet.apps.eighth.models import EighthActivity, EighthActivitySimilarity


class Command(BaseCommand):
    help = "Generate similarities for all activities"

    def add_arguments(self, parser):
        parser.add_argument("--run", action="store_true", dest="run", default=False, help="Run.")

    def handle(self, *args, **options):
        def update_sim_activity(act, act2, count):
            sim_object = EighthActivitySimilarity.objects.filter(activity_set__id=act.id).filter(activity_set__id=act2.id)
            if sim_object.exists():
                sim = sim_object.first()
                sim.count += count
            else:
                sim = EighthActivitySimilarity.objects.create(count=0, weighted=0)
                sim.activity_set.add(act, act2)
                sim.count = count
            sim.save()

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
        all_users = {u.id: u for u in get_user_model().objects.all()}
        for act in acts:
            start_act = time.time()
            freq_users = act.frequent_users
            grade_distribution = [0, 0, 0, 0]
            act2_ratios_map = {}
            for u_info in freq_users:
                u_id = u_info["eighthsignup_set__user"]
                user = all_users.get(u_id)
                grade_distribution[user.grade_number - 9] += 1
                for act_info in user.frequent_signups.exclude(scheduled_activity__activity=act):
                    act_id = act_info["scheduled_activity__activity"]
                    act2 = EighthActivity.undeleted_objects.get(id=act_id)
                    if act_id not in act2_ratios_map:
                        act2_distribution = [0, 0, 0, 0]
                        freq2_users = act2.frequent_users
                        for u2_info in freq2_users:
                            u2_id = u2_info["eighthsignup_set__user"]
                            user2 = all_users.get(u2_id)
                            act2_distribution[user2.grade_number - 9] += 1
                        ratios = list(map(lambda n: n / (len(freq2_users) or 1), act2_distribution))
                        act2_ratios_map[act_id] = ratios
                    update_sim_activity(act, act2, 1)
            grade_ratios = list(map(lambda n: n / (len(freq_users) or 1), grade_distribution))
            for act2_id, eighth_ratios in act2_ratios_map.items():
                if abs(max(eighth_ratios) - max(grade_ratios)) <= 0.1:
                    act2 = EighthActivity.undeleted_objects.get(id=act2_id)
                    update_sim_activity(act, act2, 2)
            direct_acts = EighthActivity.objects.filter(sponsors__in=act.sponsors.all()).exclude(id=act.id).distinct()
            for direct_act in direct_acts:
                update_sim_activity(act, direct_act, 2)
            all_departments = []
            for sponsor in act.sponsors.all():
                if sponsor.department not in all_departments:
                    all_departments.append(sponsor.department)
            department_acts = EighthActivity.objects.filter(sponsors__department__in=all_departments).exclude(id=act.id).distinct()
            for department_act in department_acts:
                update_sim_activity(act, department_act, 1)
            print(f"Finished similarities for {act} in {time.time() - start_act} seconds")
        for act in acts:
            if act.is_popular:
                for sim in act.similarities.all():
                    sim.count *= 2
                    sim.save()
        all_sim_acts = EighthActivitySimilarity.objects.all()
        for sim in all_sim_acts:
            sim.update_weighted()
            print(f"Similarity of {sim}")
        print(f"Number of similar activities: {len(all_sim_acts)}")
        print(f"Generated similarities in {time.time() - start} seconds")
