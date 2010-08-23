#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from models import *
from locations.models import *
from reporters.models import *

admin.site.register(OTPSite)
admin.site.register(OTPReporter)


#admin.site.register(LocationType)

admin.site.register(HealthPost)

admin.site.register(Entry)

admin.site.register(WebUser)
admin.site.register(ReportPeriod)
