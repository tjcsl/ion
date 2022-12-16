# Ion Fake Data

A set of scripts to generate somewhat realistic student data for the Ion development environment. This is run automatically on initial Docker setup. To run manually, follow the instructions below:

## Usage

- To re-run initial configuration tasks (including importing development data), delete `config/docker/first-run.log` and restart the container. This will load the same data as during the initial run.
- To run manually and/or change data:

  - Delete `config/docker/first-run.log`
  - Then, either:
    - Restart the container to load new data
    - Or manually run `config/docker/initial_setup.sh`
- To run a specific script:

  - `python config/scripts/create_users.py` - Generates fake student, admin, and teacher data. For specific usage run `pythons create_users.py -h`
  - `python config/scripts/create_activities.py` - Generates fake eighth activity data using fake user data. For specific usage run `python create_activites.py -h`
  - `python config/scripts/create_blocks.py` - Generates fake eighth blocks using using fake user and activity data. For specific usage run `python create_blocks.py -h`

#### Additional data generation (not using these scripts):

- Keep in mind all of these are done automatically on initial setup.

5. Creating eighth period blocks:

* Run `python manage.py dev_create_blocks MM/DD/YYYY` with the date to generate blocks until.

6. Pull sports schedules

* Run `python manage.py import_sports MONTH` to pull sports schedules for the month.
* Note this is automatically done for you each month.