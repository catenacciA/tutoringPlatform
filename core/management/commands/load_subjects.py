from django.core.management.base import BaseCommand, CommandError
from core.models import Subject
from pathlib import Path
import csv
import os

# Adjust the FILEPATH to point to core/management/subjects.csv
FILENAME: str = "subjects.csv"
FILEPATH: str = os.path.join(
    Path(__file__).resolve().parent.parent,  # This goes up to the core directory
    FILENAME
)

CORE_SUBJECTS = ['Math', 'Physics', 'Chemistry']


def cleanup() -> None:
    # Delete all subjects that are not core subjects
    Subject.objects.exclude(name__in=CORE_SUBJECTS).delete()


class Command(BaseCommand):
    help = "Populates DB with subjects from a CSV file"

    def handle(self, *args, **options):
        cleanup()
        self.populate()

    def populate(self) -> None:
        if not os.path.exists(FILEPATH):
            raise CommandError(f"File {FILEPATH} does not exist")

        with open(FILEPATH, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            if 'name' not in reader.fieldnames:
                raise CommandError("CSV file must have a 'name' column")

            for row in reader:
                subject_name = row['name']
                if subject_name:
                    Subject.objects.get_or_create(name=subject_name)
                    self.stdout.write(self.style.SUCCESS(f'Successfully added/updated subject: {subject_name}'))

        if Subject.objects.count() <= 0:
            raise CommandError("Population failed. No subjects inserted in DB.")
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully populated DB with {Subject.objects.count()} subjects"))
