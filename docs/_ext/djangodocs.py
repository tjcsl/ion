# -*- coding: utf-8 -*-
def setup(app):
    """Setup for djangodocs."""
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )
