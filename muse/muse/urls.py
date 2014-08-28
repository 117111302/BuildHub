from django.conf.urls import patterns, include, url
from django.contrib import admin

from core import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'muse.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns(views,
    url(r'^$', views.login),
#    url(r'^(\w+)/', views.index),
    url(r'^oauth_callback/', views.oauth_callback),
    url(r'^payload/', views.payload),
    url(r'^create_hook/', views.create_hook),
    url(r'^repo/(\w+)/$', views.repo),
    url(r'^badge/(\w+)/(\w+)/$', views.badge),
    url(r'^(\w+)/builds/(\d+)/$', views.builds),
    url(r'^stream/', views.stream_view),
)
