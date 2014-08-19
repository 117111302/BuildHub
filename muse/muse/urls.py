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
    url(r'^index', views.index),
    url(r'^oauth_callback/', views.oauth_callback),
    url(r'^payload/', views.payload),
)
