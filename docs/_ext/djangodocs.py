def setup(app):
	"""
		Setup for django docs.
	"""
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )
