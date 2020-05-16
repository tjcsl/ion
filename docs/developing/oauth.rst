***********
Using OAuth
***********

With the Django OAuth Toolkit, Ion supports accessing API and other resources via OAuth2. This allows for applications to be written using the Ion API without the need to prompt for user credentials from within the application. Instead, access tokens are used to gain access to Ion API resources.

For more details on OAuth, please refer to https://oauth.net.

**Note**: All of the examples on the page are targeted towards web applications. They will not work for the purposes of, for example, allowing a program running on your computer to access the Ion API.

Register an application
=======================

Go to https://ion.tjhsst.edu/oauth/applications/ and log in to create and register a client application. Specify the following values in the form, as prompted:

Name
 * Some descriptive name for your application.
Client Type*
 * Choose "Confidential" if your app has a backend component and your server can store the client ID and secret securely
 * Choose "Public" if your app is purely client-side and a copy of the credentials will be distributed publicly
Authorization Grant Type*
 * Choose "Authorization code" if your client type is "Confidential"
 * Choose "Implicit" if your client type is "Public" (for example, on a native application)
Redirect URIs
 * Enter one or more URLs that your application will redirect back to after the authorization is completed.

Store the Client ID and Client Secret tokens for use with your application.

* These are the recommended settings. For a better understanding of which settings you should choose, read this `introduction to OAuth <https://aaronparecki.com/oauth-2-simplified/>`_ and this `guide to grant types <https://alexbilbie.com/guide-to-oauth-2-grants/>`_.

Requesting authorization
========================

Inside your application, redirect to the OAuth authorization endpoint to receive an authorization code. The URL is https://ion.tjhsst.edu/oauth/authorize/

To access the API, exchange this code for a (temporary) access token. The URL is https://ion.tjhsst.edu/oauth/token/.

Python-social-auth
------------------

If you want to use ``python-social-auth``, a plugin is available in the `ion_oauth <https://pypi.python.org/pypi/ion_oauth>`_ package. Note that it is not currently actively maintained by the Ion development team and thus may require modification to work properly.

For a Django project, add ``AUTHENTICATION_BACKENDS = ['ion_oauth.oauth.IonOauth2']`` and define ``SOCIAL_AUTH_ION_KEY`` and ``SOCIAL_AUTH_ION_SECRET`` in your settings.py file.

For additional guidance, refer to `the official documentation <https://python-social-auth.readthedocs.io/en/latest/>`_, using *Ion* as the OAuth backend.

Python
------

For a Python client, use requests with requests-oauthlib.

If running locally (without HTTPS), override the SSL requirement for OAuth2.

    >>> import os
    >>> os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

Create an OAuth2Session, with the CLIENT_ID and REDIRECT_URI you entered in the application form. Redirect the user to authorization_url.

    >>> from requests_oauthlib import OAuth2Session
    >>> oauth = OAuth2Session(CLIENT_ID,
    >>>                       redirect_uri=REDIRECT_URI,
    >>>                       scope=["read","write"])
    >>>
    >>> authorization_url, state = oauth.authorization_url("https://ion.tjhsst.edu/oauth/authorize/")

The user authenticates, approves the request, and is redirected to the callback URL specified in redirect_uri, with a "code" GET parameter.

    >>> token = oauth.fetch_token("https://ion.tjhsst.edu/oauth/token/",
    >>>                           code=CODE,
    >>>                           client_secret=CLIENT_SECRET)
    >>> print(token)
    {'refresh_token': 'XXX', 'access_token': 'XXX', 'expires_in': 36000, 'expires_at': 1455370143.573362, 'scope': ['read', 'write'], 'token_type': 'Bearer'}

At this point, a valid access token has been gained, and you can request API resources.

.. code-block:: python

    try:
        profile = oauth.get("https://ion.tjhsst.edu/api/profile")
    except TokenExpiredError as e:
        args = { "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET }
        token = oauth.refresh_token("https://ion.tjhsst.edu/oauth/token/", **args)

    import json
    print(json.loads(profile.content.decode()))
    { 'ion_username': '2016jwoglom', ... }

After 36,000 seconds (1 hour), the token will expire; you need to renew it. This can be handled by putting API commands inside a try-except for a oauthlib.oauth2.TokenExpiredError, such as seen above. Alternatively, you can provide "auto_refresh_url=refresh_url, auto_refresh_kwargs=args" as additional arguments to OAuth2Session when it is created.

.. code-block:: python

     args = { "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET }
     token = oauth.refresh_token("https://ion.tjhsst.edu/oauth/token/", **args)

Node.js
-------

You can use the `simple-oauth2 <https://github.com/lelylan/simple-oauth2>`_ library to perform authentication. Below is some sample code.

**Note**: This code will not work out of the box. Read the comments carefully to determine how to integrate it into your application.

.. code-block:: javascript

    var simpleoauth2 = require("simple-oauth2");

    // make sure these variables are set
    var ion_client_id = process.env.ION_CLIENT_ID;
    var ion_client_secret = process.env.ION_CLIENT_SECRET;
    var ion_redirect_uri = process.env.ION_REDIRECT_URI;

    var oauth = simpleoauth2.create({
        client: {
            id: ion_client_id,
            secret: ion_client_secret
        },
        auth: {
            tokenHost:     'https://ion.tjhsst.edu/oauth/',
            authorizePath: 'https://ion.tjhsst.edu/oauth/authorize',
            tokenPath:     'https://ion.tjhsst.edu/oauth/token/'
        }
    });

    // 1) when the user visits the site, redirect them to login_url to begin authentication
    var login_url = oauth.authorizationCode.authorizeURL({
        scope: "read", // remove scope: read if you also want write access
        redirect_uri: ion_redirect_uri
    });

    // 2) on the ion_redirect_uri endpoint, add the following code to process the authentication
    var code = req.query["code"]; // GET parameter
    oauth.authorizationCode.getToken({code: code, redirect_uri: ion_redirect_uri}).then((result) => {
        const token = oauth.accessToken.create(result);

        // you will want to save these variables in your session if you want to make API requests
        var refresh_token = token.token.refresh_token;
        var access_token = token.token.access_token;
        var expires_in = token.token.expires_in;

        // log the user in
    });

    // 3) when making an API request, add the following header:
    // Authorization: Bearer {{ INSERT ACCESS TOKEN }}

    // 4) to refresh the access_token, use the following code
    var token = oauth.accessToken.create({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in
    });

    if (token.expired()) {
        token.refresh((err, result) => {
            token = result;
            // the new access token
            var access_token = token.token.access_token;
        });
    }
