import datetime
import os
import subprocess

today = datetime.date.today()
now = datetime.datetime.now()

first_run = not os.path.exists("config/logs/initial-setup.log")
sports_monthly_run = os.path.exists("config/logs/sports-" + now.strftime("%B").lower() + ".log")


def run(command):
    print(subprocess.run(command, check=True, stdout=subprocess.PIPE).stdout.decode("utf-8"))


def pull_sports(first_setup=False):
    print("Pulling sports schedules for " + today.strftime("%B") + "...")
    run(["./manage.py", "import_sports", str(today.month)])

    print("Writing to new sports log file...")
    with open("config/logs/sports-" + now.strftime("%B").lower() + ".log", "w", encoding="utf8") as f:
        f.write("Sports schedules have been pulled for " + today.strftime("%B") + ".")
        f.write("\nDelete this file to re-pull sports schedules on next startup.")

    if not first_setup:
        first = today.replace(day=1)
        last_month = first - datetime.timedelta(days=1)
        print("Removing old sports log file...")
        os.remove("config/logs/sports-" + last_month.strftime("%B").lower() + ".log")


def initial_setup():
    print("---- Running initial setup tasks -----")
    print("This may take a while.")

    print("Allowing execution of scripts...")
    run(["chmod", "+x", "config/docker/initial_setup.sh"])
    run(["chmod", "+x", "config/data/generate_data.sh"])

    print("Running initial setup script...")
    run(["config/docker/initial_setup.sh"])

    print("Creating additional class-year students...")
    for i in range(today.year, today.year + 8):
        run(["python3", "create-users.py", "-s", str(i) + "student"])

    print("Creating eighth period blocks until" + " 07/01/" + str(today.year + 3) + "...")
    run(["./manage.py", "dev_create_blocks", "07/01/" + str(today.year + 3)])

    pull_sports(first_setup=True)

    with open("config/logs/initial-setup.log", "w", encoding="utf8") as f:
        f.write("Initial setup: " + now.strftime("%Y-%m-%d %H:%M:%S") + " UTC")
        f.write("\nDelete this file to re-run initial setup tasks on next startup.")

    print("Data generation complete.")
    print()
    print("---- Completed initial setup. ----")
    print("Run './create-users.py -a [USERNAME]' to create an admin user for yourself.")
    print("Alternatively, login with username 'admin' and password 'notfish'")
    print()


if first_run:
    initial_setup()

if not sports_monthly_run and not first_run:
    pull_sports()
