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
    url(r'^$', views.login_view),
#    url(r'^(\w+)/', views.index),
    url(r'^logout/$', views.logout_view),
    url(r'^signin/', views.signin),
    url(r'^auth/$', views.auth),
    url(r'^index/', views.index),
    url(r'^repos/', views.repos),
    url(r'^payload/', views.payload),
    url(r'^create_hook/', views.create_hook),
    url(r'^edit_hook/', views.edit_hook),
    url(r'^repo/(\w+)/$', views.repo),
    url(r'^badge/(\w+)/(\w+)/$', views.badge),
    url(r'^(\w+)/builds/$', views.builds),
    url(r'^(\w+)/builds/(\d+)/$', views.get_build),
    url(r'^stream/', views.stream_view),
)
