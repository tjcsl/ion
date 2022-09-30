# Ion Fake Data

A set of scripts to generate somewhat realistic student data for the Ion development environment. This is run automatically on initial Docker setup. To run manually, follow the instructions below:

## Usage

- To re-run initial configuration tasks (including importing development data), delete `config/docker/first-run.log` and restart the container. This will load the same data as during the initial run.
- To run manually and/or change data:

  - Run `config/data/generate_data.sh`
  - Then, either:
    - Delete `config/docker/first-run.log` and restart the container to load new data
    - Or continue to the Import to Ion section to import manually
- To run a specific script:

  - `python fake_user.py` - Generates fake student and teacher data.  Stores in outputs subdirectory.
  - `python fake_activities.py` - Generates fake eighth activity data using fake user data.  Stores in outputs subdirectory.

## Importing to Ion

1. Import user data (`user_import.json`)

* Run `python manage.py import_users config/data/outputs/user_import.json`

2. Import eighth activities (`eighth_import.json`)

* Run `python manage.py import_eighth config/data/outputs/eighth_import.json`

---

#### Additional data generation (not using these scripts):

- Keep in mind all of these are done automatically on initial setup.

5. Creating eighth period blocks:

* Run `python manage.py dev_create_blocks MM/DD/YYYY` with the date to generate blocks until.

6. Pull sports schedules

* Run `python manage.py import_sports MONTH` to pull sports schedules for the month.
* Note this is automatically done for you each month.

## Sources

* List of first names from the Social Security for births between from 1880 to 2016.
