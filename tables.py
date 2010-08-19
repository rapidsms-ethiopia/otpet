#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import django_tables as tables


class HealthPostsTable(tables.Table):
    pk = tables.Column(visible=False, sortable=False)
    code = tables.Column(verbose_name=u"Code")
    name = tables.Column(verbose_name=u"Name")
    woreda = tables.Column(verbose_name=u"Woreda")
    zone = tables.Column(verbose_name=u"Zone")
    region = tables.Column(verbose_name=u"Region")
    reporter = tables.Column(verbose_name=u"Reporter")
    last = tables.Column(verbose_name=u"Last Report", sortable=False)
    last_pk = tables.Column(visible=False, sortable=False)
    last_sort = tables.Column(visible=False)
    last_color = tables.Column(sortable=False, visible=False)


class HealthWorkersTable(tables.Table):
    pk = tables.Column(visible=False, sortable=False)
    alias = tables.Column(verbose_name=u"Alias")
    name = tables.Column(verbose_name=u"Name")
    hp = tables.Column(verbose_name=u"Health Post")
    hp_pk = tables.Column(visible=False, sortable=False)
    contact = tables.Column(verbose_name=u"Contact", sortable=False)

class EntryTable(tables.Table):
    pk = tables.Column(visible=False, sortable=False)
    otp_reporter = tables.Column(verbose_name = u"Reporter")
    health_post = tables.Column(verbose_name = u"OTP Site")
    hp_pk = tables.Column(visible=False, sortable=False)
    new_admission = tables.Column(verbose_name = u"New")
    cured = tables.Column(verbose_name = u"Cured")
    died = tables.Column(verbose_name = u"Dead")
    defaulted = tables.Column(verbose_name = u"Defalters")
    non_responded = tables.Column(verbose_name = u"Non Responded")
    medical_transfer = tables.Column(verbose_name = u"Medical Transfer")
    tfp_transfer = tables.Column(verbose_name = u"TFP Transfer")
    entry_time = tables.Column(verbose_name = u"Sent on")

class AlertTable(tables.Table):
    #pk = tables.Column(visible=False, sortable=False)
    notice = tables.Column(name = u"Alert Message")
    resolved = tables.Column(name = u"Is Resolved")
    time = tables.Column(name = u"Time")
    otp_reporter = tables.Column(name = u"Reported By")

class RepHealthPostTable(tables.Table):
    #pk = tables.Column(visible=False, sortable=False)
    name = tables.Column(name = u"Name")
    code = tables.Column(name = u"Code")
    type = tables.Column(name = u"Type")
    child_number = tables.Column(name = u"Number of Child Locations")
    parent_name = tables.Column(name = u"Parent Location Name")
    
    

    
