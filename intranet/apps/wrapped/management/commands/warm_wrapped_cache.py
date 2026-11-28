import time

from django.core.management.base import BaseCommand

from intranet.apps.wrapped.stats import (
    compute_signup_counts,
    compute_unique_activity_counts,
    compute_visit_counts,
    set_cached_cohort_counts,
)
from intranet.utils.date import get_date_range_this_year, get_school_year_label


class Command(BaseCommand):
    help = "Warm Ion Wrapped cohort caches used for percentile/rank calculations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-visits",
            action="store_true",
            default=False,
            help="Warm only 8th period cohort caches and skip the request-log visit distribution.",
        )

    def warm_distribution(self, label, cache_name, start, end, compute_counts):
        self.stdout.write(f"{label}: computing...")
        started = time.monotonic()
        counts = set_cached_cohort_counts(cache_name, start, end, compute_counts())
        elapsed = time.monotonic() - started
        self.stdout.write(self.style.SUCCESS(f"{label}: cached {len(counts)} values in {elapsed:.1f}s."))

    def handle(self, *args, **options):
        start, end = get_date_range_this_year()
        start_date = start.date()
        end_date = end.date()
        year_label = get_school_year_label()

        self.stdout.write(f"Warming Ion Wrapped cohort caches for {year_label}.")
        self.stdout.write(f"Date range: {start.isoformat()} through {end.isoformat()}")

        self.warm_distribution(
            "8th period signup counts",
            "signup-counts",
            start_date,
            end_date,
            lambda: compute_signup_counts(start_date, end_date),
        )
        self.warm_distribution(
            "Unique activity counts",
            "unique-activity-counts",
            start_date,
            end_date,
            lambda: compute_unique_activity_counts(start_date, end_date),
        )

        if options["skip_visits"]:
            self.stdout.write(self.style.WARNING("Skipping Ion visit counts. Visit percentile labels will be omitted until this cache is warmed."))
        else:
            self.stdout.write("Ion visit counts use request logs and may take noticeably longer than the 8th period caches.")
            self.warm_distribution(
                "Ion visit counts",
                "visit-counts",
                start,
                end,
                lambda: compute_visit_counts(start, end),
            )

        self.stdout.write(self.style.SUCCESS("Ion Wrapped cohort cache warm complete."))
