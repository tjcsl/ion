from django.conf.urls import patterns, url
from .apps.users.auth.views import index, login_view, info, logout_view

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

#urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'intranet.views.home', name='home'),
    # url(r'^intranet/', include('intranet.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
#)

urlpatterns = patterns('auth.views.',
    url(r'^$', index),
    url(r'^login$', login_view),
    url(r'^info$', info),
    url(r'^logout$', logout_view),
)
