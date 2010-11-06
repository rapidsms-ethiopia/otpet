from django.conf.urls.defaults import *
import os
import otpet.views as views

urlpatterns = patterns("",

    #Dashboard - Index
    (r'^$', views.index),
	(r'^otp/$', views.index),

    #Reporters
    (r'^otp/reporter/(?P<reporter_id>\d+)/$', views.reporter), 
    (r'^otp/health_workers/$', views.reporters_view),
    
    #Dashboard piechart
    (r'^pie.png$', views.reports_pie),
    (r'^otp/pie.png$', views.reports_pie),
    
    #OTP reports...
    (r'^otp/otpreports/$', views.reports_view),
    (r'^otp/report/$', views.report_view),
    
    #OTP Charts
    (r'^otp/otpchart/$', views.charts),
    
    #OTP Health Posts
	(r'^otp/health_posts$', views.healthposts_view),
	(r'^otp/health_post/(\d+)$', views.healthpost_view),
    
    #Maps
    (r'^otp/maps$', views.map_entries),
    
    # Send SMS message to reporters 
    (r'^otp/send_sms/$', views.send_sms),
     
    
	
	
)

