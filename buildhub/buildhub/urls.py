from django.conf.urls import patterns, include, url
from django.contrib import admin

from core import views

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns(views,
    url(r'^$', views.login_view),
    url(r'^logout/$', views.logout_view),
    url(r'^login/$', views.login_view),
    url(r'^register/$', views.register),
    url(r'^keygen/$', views.keygen),
    url(r'^groups/$', views.groups),
    url(r'^group/$', views.group),
    url(r'^index/$', views.index),
    url(r'^repos/$', views.repos),
    url(r'^(?P<repo>(.+?)/(.+?))/builds/(?P<build_id>\d+)/$', views.get_build),
    url(r'^(?P<repo>(.+?)/(.+?))/builds/$', views.builds),
    url(r'^(?P<repo>(.+?)/(.+?))/$', views.repo),
)
