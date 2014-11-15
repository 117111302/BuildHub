from django.conf.urls import patterns, include, url
from django.contrib import admin

from core import views

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns(views,
    url(r'^$', views.index),
    url(r'^logout/$', views.logout_view),
    url(r'^login/$', views.login_view),
    url(r'^index/$', views.index),
    url(r'^register/$', views.register),
    url(r'^keygen/$', views.keygen),
    url(r'^test/$', views.test),
    url(r'^servers/$', views.servers),
    url(r'^add_server/$', views.add_server),
    url(r'^keys/$', views.keys),
    url(r'^groups/$', views.groups),
    url(r'^add_group/$', views.add_group),
    url(r'^groups/(?P<name>(.+?))/$', views.index),
    url(r'^add_repos/$', views.add_repos),
    url(r'^del_repos/$', views.del_repos),
    url(r'^repos/$', views.repos),
    url(r'^(?P<repo>(.+?)/(.+?))/builds/(?P<build_id>\d+)/$', views.get_build),
    url(r'^(?P<repo>(.+?)/(.+?))/builds/$', views.builds),
    url(r'^(?P<repo>(.+?)/(.+?))/$', views.repo),
)
