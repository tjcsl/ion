# This file contains logic for server-side rendered pages


def hello_world(page, sign):
    return {"message": "{} from {} says Hello".format(page.name, sign.name)}
