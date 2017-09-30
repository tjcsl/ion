import datetime

from faker import Faker

from ...models import User
fake = Faker()


def generate_fake(users, modify=False):
    for user in users:
        print("Faking {}".format(user.username))
        if user.username in ["2018nzhou", "2019okulkarn", "2018wzhang", "2020djones", "2020klanzill"]:
            print("Skipping {}".format(user))
            continue
        # User fields
        if user.gender:
            user.first_name = fake.first_name_male()
            user.last_name = fake.last_name()
        else:
            user.first_name = fake.first_name_female()
            user.last_name = fake.last_name()
        user.middle_name = fake.color_name()
        if user.nickname is not None:
            user.nickname = fake.safe_color_name()
        if user.user_type == 'student':
            user.username = "{}{}{}".format(user.username[:4], user.first_name[0], user.last_name[:7]).lower()
            if user.graduation_year is None:
                user.graduation_year = 2020
            try:
                possible_start = datetime.date(user.graduation_year - 19, 8, 1)
                possible_end = datetime.date(user.graduation_year - 18, 5, 30)
                user.properties._birthday = fake.date_between_dates(date_start=possible_start, date_end=possible_end)
            except:
                # TODO: maybe handle this sometime. Right now it doesn't matter that much.
                pass
        else:
            user.username = "{}{}{}".format(user.first_name[0], user.middle_name[0], user.last_name).lower()
            user.properties._birthday = fake.date_between_dates(date_start=datetime.date(1955, 1, 1), date_end=datetime.date(1985, 12, 31))

        ct = 1
        base_username = user.username
        while True:
            if not User.objects.filter(username=user.username).exists():
                break
            user.username = "{}{}".format(base_username, ct)
            ct += 1
        if modify:
            user.save()

        print(user)

        # Phone numbers
        for phone in user.phones.all():
            num = fake.phone_number()[:12]
            num.replace('.', '-')
            phone._number = num
            if modify:
                phone.save()
            print("{}: {}".format(phone.get_purpose_display(), phone._number))

        # Email addresses
        for email in user.emails.all():
            email.address = fake.free_email()
            if modify:
                email.save()

        for website in user.websites.all():
            website.url = fake.url()
            if modify:
                website.save()

        # Delete all photos until I maybe
        # figure out how to use fake photo binaries
        for photo in user.photos.all():
            photo.delete()

        # Address
        address = user.properties._address
        if address is not None:
            address.street = fake.street_address()
            address.city = fake.city()
            address.state = fake.state()
            address.postal_code = fake.postalcode()
            if modify:
                address.save()
