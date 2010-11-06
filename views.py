#!/usr/bin/env python
# vim: noet

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect

from datetime import datetime, timedelta
import fpformat
import os
import sys
import math

#from pygooglechart import SimpleLineChart, Axis, PieChart2D, StackedVerticalBarChart

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.management import setup_environ

from models import *
from utils import * 

from tables import *
import django_tables as tables
from scope import *

from matplotlib.backends.backend_agg import FigureCanvasAgg as  FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import matplotlib as mpl
mpl.rcParams['font.size'] = 7
import matplotlib.pyplot as plt

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from pylab import *
#import random

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure


@login_required
@define_scope
def index(request,scope):
    '''Display home page / Dashboard'''
    #initially set the current reporting period
    month, year, late , dates_gc = current_reporting_period()
    current_period = get_or_generate_reporting_period()
    #get the entries collected by the current period
    entries = scope.current_entries()
    
    
    summary = {}
    summary['pk'] = current_period.pk
    #Period in gregorian calander
    summary['periodgc'] = (dates_gc[0],dates_gc[1]) 
    #period in Ethiopian calander
    summary['period'] = "%s, %s" %(month, year)
    #Total Health Posts (under the Web Users location)
    summary['health_posts'] = len(scope.health_posts())
    #View only datas that has been confirmed by users under the users hierarchy
    #woreda > zone > region > federal
    wcount = 0
    zcount = 0
    rcount = 0
    c = 0
    try:
        
        all_entries = scope.entries()
        entries_in_currentperiod = filter(lambda all_entries: all_entries.report_period == current_period, all_entries)
        
        for entry in entries_in_currentperiod:
            c = c +1
            if entry.confirmed_by_woreda==False:
                wcount = wcount + 1
            if entry.confirmed_by_zone==False and entry.confirmed_by_woreda==True:
                zcount = zcount + 1
            if entry.confirmed_by_region==False and entry.confirmed_by_zone==True:
                rcount = rcount + 1
                    
    except:
        pass
            
    summary['unconfirmed_woreda'] = wcount
    summary['unconfirmed_zone'] = zcount
    summary['unconfirmed_region'] = rcount
    
    
    if entries is not None:
        count = 0
        
        for entry in entries:
            if entry.confirmed_by_woreda==True and scope.location.type.name=='woreda':
                count = count + 1
            elif entry.confirmed_by_zone==True and scope.location.type.name=='zone':
                count = count + 1
            elif entry.confirmed_by_region==True and scope.location.type.name=='region':
                count = count + 1
                
        
                
        summary['confirmed'] = count
        summary['completed'] = len(entries)
        summary['missing'] = len(scope.health_posts()) - summary['completed']
        
        try:
            summary['percent'] = round(float(summary['completed']) / float(len(scope.health_posts())) * 100.0)
        except:
            summary['percent'] = 0
    
    
    #get the current alerts accepted
    notifications = scope.alerts()
    notifications = filter(lambda notifications: notifications.resolved == False, notifications)
    # paginaging for notifications
    paginator_alert = Paginator(notifications, 10)
    
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    
    try:
        notifications =  paginator_alert.page(page)
    except (InvalidPage, EmptyPage):
        notifications = paginator_alert.page(paginator_alert.num_pages)
        
    # if message is sent from the form, send it via send_text_message()
    message = ""
    reporter_received = []
    reporter_not_received = []
    recipients = []
    errors = []
    if request.method == 'POST':
        sms_text = request.POST['message'].replace('\n', '')
        
        reporters = scope.otp_reporters()
        for reporter in reporters:
            if request.POST.has_key("reporter-" + str(reporter.pk)):
                recipients.append(reporter)
        
        if sms_text == "":
            errors.append('Please Enter Your Message.')
        elif len(recipients) == 0:
            errors.append('Please Select Contacts.')
        else:
            (message, reporter_received, reporter_not_received) = send_text_message(recipients, sms_text)
            

    try:
        sum={}
        all = []
        for entry in entries:
            ent={}
            ent['pk'] = entry.pk
            ent['otp_reporter'] = entry.otp_reporter
            ent['health_post'] = entry.health_post
            ent['hp_pk'] = entry.health_post.pk
            ent['new_admission'] = entry.new_admission
            ent['cured'] = entry.cured
            ent['died'] = entry.died
            ent['defaulted'] = entry.defaulted
            ent['non_responded'] = entry.non_responded
            ent['medical_transfer'] = entry.medical_transfer
            ent['tfp_transfer'] = entry.tfp_transfer
            ent['entry_time'] = convertToHumanReadable(entry.entry_time)
            ent['confirmed'] = entry.confirmed_by_woreda
            all.append(ent)
            table = EntryTable(all, order_by=request.GET.get('sort'))
            entry_rows = table.rows
            
            paginator = Paginator(entry_rows, 10)
            
            try:
                page = int(request.GET.get('page', '1'))
            except ValueError:
                page = 1
            
            try:
                entry_rows =  paginator.page(page)
            except (InvalidPage, EmptyPage):
                entry_rows = paginator.page(paginator.num_pages)
                  
            summary['entry_rows'] = entry_rows
            
            
        return render_to_response('otp/index.html',
                                  {"reporters": scope.otp_reporters(),
                                   "webuser_location": scope.location, 
                                   
                                   "summary" : summary, 
                                   "table": table , 
                                   "scope":scope, 
                                   "notifications":notifications,
                                   'message':message,
                                   'reporter_received':reporter_received,
                                   'reporter_not_received':reporter_not_received,
                                   'success':len(reporter_received), 
                                   'failure':len(reporter_not_received),
                                   'total_reporters_sms': len(recipients),
                                   'errors':errors},
                                   
                                   context_instance=RequestContext(request))
    except:
        table = EntryTable(all, order_by=request.GET.get('sort'))
        return render_to_response('otp/index.html',{"notifications":notifications,
                                                    "reporters": scope.otp_reporters(),
                                                    "webuser_location": scope.location,
                                                    "summary" : summary ,"table": table ,
                                                    "scope":scope,
                                                    'message':message,
                                                    'reporter_received':reporter_received,
                                                    'reporter_not_received':reporter_not_received,
                                                    'success':len(reporter_received), 
                                                    'failure':len(reporter_not_received),
                                                    'total_reporters_sms': len(recipients),
                                                    'errors':errors},
                                                    context_instance=RequestContext(request))


#Map Entris for Kombolcha & Haromaya.
#@csrf_exempt
#@login_required
#@define_scope
#def map_entries(request, scope):
#    entries = scope.entries()
#    webuser = WebUser.by_user(request.user)
#    webuser_location = webuser.location
#    # currently the map is only for two woredas
#    location_types = ["woreda"]
#    location_names = []
#    locations = scope.health_posts()
#    #filter locations which are health posts only
#    healthposts = filter(lambda locations: locations.type.name.lower() == "health post", locations)
#
#    # filter current period entries
#    current_period = get_or_generate_reporting_period()
#    entries_in_currentperiod = filter(lambda entries: entries.report_period == current_period, entries)
#    
#    late_healthposts = HealthPost.get_late_healthposts(scope=scope, current_period=current_period)       
#    
#    
#    result_dic = {"entries": entries_in_currentperiod, "location_types":location_types,
#                  'webuser_location':webuser_location,
#                  'late_healthposts':late_healthposts}
#    
#    woreda_selected = ""
#    if request.method == 'POST':
#        woreda_selected = request.POST['location_name']
#
#    if webuser_location is not None:
#            if webuser_location.type.name.lower() == "woreda":
#                    location_names.append(webuser_location.name)
#                    result_dic["location_names"] = location_names
#                    if webuser_location.name.lower() == "haromaya":
#                            return render_to_response("otp/map_image_haromaya.html",
#                                      result_dic,
#                                      context_instance=RequestContext(request))
#                    
#                    elif webuser_location.name.lower() == "kombolcha":
#                            return render_to_response("otp/map_image_kombolcha.html",
#                                      result_dic,
#                                      context_instance=RequestContext(request))
#                    
#            else:
#                    location_names.append("Haromaya")
#                    location_names.append("Kombolcha")
#                    result_dic["location_names"] = location_names
#                                                                  
#                    return render_to_response("otp/map_image_haromaya.html" if woreda_selected.lower() == "haromaya"
#                                              else "otp/map_image_kombolcha.html",
#                                              result_dic,
#                                              context_instance=RequestContext(request))

@login_required
@define_scope
def map_entries(request, scope): 
    #entries_confirmed = None     
    def has_coords(entry):
        loc = entry.health_post
        if loc is None: return False
        return  (loc.latitude is not None) and (loc.longitude is not None)

    webuser_location = scope.location
    # filter current period entries
    entries = scope.entries()
    current_period = get_or_generate_reporting_period()
    entries = filter(lambda entries: entries.report_period == current_period, entries)

    # then filter confirmed entries
    if webuser_location.type.name.lower() == "zone":
        entries_confirmed = filter(lambda entries: entries.confirmed_by_woreda == True, entries)
            
    elif webuser_location.type.name.lower() == "region":
        entries_confirmed = filter(lambda entries: entries.confirmed_by_woreda == True and
                                       entries.confirmed_by_zone == True, entries)
                            
    elif webuser_location.type.name.lower() == "federal":
        entries_confirmed = filter(lambda entries: entries.confirmed_by_woreda == True and
                                       entries.confirmed_by_zone == True and
                                      entries.confirmed_by_region == True, entries)
    elif webuser_location.type.name.lower() == "woreda":
        entries_confirmed = entries
    else:
        entries_confirmed = filter(lambda entries: entries.confirmed_by_woreda == True and
                                       entries.confirmed_by_zone == True and
                                      entries.confirmed_by_region == True, entries)
    # health posts
    health_posts = scope.health_posts()
    health_posts = filter(lambda health_posts:(health_posts.latitude is not None) and (health_posts.longitude is not None),health_posts)
    health_posts_withentry = []
    health_posts_noentry = []
    for ent in entries_confirmed:
        health_posts_withentry.append(ent.health_post)
        
    for hp in health_posts:
        if hp not in health_posts_withentry:
            health_posts_noentry.append(hp)
            
    health_posts = health_posts_noentry   
        
    
    
        
    entries_with_coordinate = filter(has_coords, entries_confirmed)
    
    print "______________________________________________________"
    print "health posts with no entry..."
    print health_posts
    print "Entries with coordinate..."
    print entries_with_coordinate
    print "______________________________________________________"
    
    return render_to_response("otp/map_entries.html",
                              {"entries": entries_with_coordinate,
                               "health_posts":health_posts},
                              context_instance=RequestContext(request))



def xhr_test(request):
    if request.is_ajax():
        if request.method == 'GET':
            message = "This is an XHR GET request"
        elif request.method == 'POST':
            message = "This is an XHR POST request"
            # Here we can access the POST data
            print request.POST
    else:
        message = "No XHR"
    return HttpResponse(message)





    
@login_required
@define_scope
def reports_pie(request,scope):

    month, year, late , dates_gc = current_reporting_period()
 
    period = (dates_gc[0],dates_gc[1])
 
    completed = len(scope.current_entries())
    incomplete = len(scope.health_posts()) - len(scope.current_entries())
 

    fig = Figure()
    ax=fig.add_subplot(111, axisbg='r')
    fig.set_figheight(2)
    fig.set_figwidth(2)
    fig.set_facecolor('w')
  
    labels = 'Completed', 'Incomlete'
    fracs = [completed,incomplete]
    explode=(0,0.01)
    pie(fracs, explode=explode, labels=None,colors=('g','r'), autopct='%1.1f%%', shadow=True)
    title('Reports..', bbox={'facecolor':'0.5', 'pad':5})
    ax.pie(fracs, explode=explode, labels=None,colors=('#52E060','#F7976E'),  shadow=True)
   
    canvas=FigureCanvas(fig)
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


	
@login_required
@define_scope
def reports_view(request, scope):
    ''' Show available reports '''

    return render_to_response('otp/otp_reports.html',
                              {'scope': scope, 'hps': HealthPost.objects.all(),
                               'periods': ReportPeriod.objects.all(),'webuser_location':scope.location},
                               context_instance=RequestContext(request))
    
    
    
@login_required
@define_scope
def report_view(request, scope):
    dates_GC = {}
    dates_EC = {}
    filter_parameters = request.GET
    model_name = "Entry" #filter_parameters['model']
#    location_type = filter_parameters['grp']
#    location_name = filter_parameters['placename']
    startmonth_id = filter_parameters['start']
    endmonth_id = filter_parameters['end']
    ##        startyear_id = filter_parameters['startyear_id']
    ##        endyear_id = filter_parameters['endyear_id']
    group_by = filter_parameters['grp'] 
    
    # if time range is not given, the report is for all periods
    start_period = ReportPeriod.objects.all().order_by("id")[0]
    end_period = ReportPeriod.objects.all().order_by("-id")[0]
    dates_GC["start"] = start_period.start_date
    dates_GC["end"] = end_period.end_date
    dates_EC["start"] = "%s %s" % (start_period.month, start_period.year)
    dates_EC["end"] = "%s %s" % (end_period.month, end_period.year) 
    
    try:
        start_period = ReportPeriod.objects.get(
                    pk=request.GET.get('start', ReportPeriod.objects.latest().id))
    except (ReportPeriod.DoesNotExist, ValueError):
        start_period = ReportPeriod.objects.latest()
    try:
        end_period = ReportPeriod.objects.get(pk=request.GET.get('end',
                                                             start_period.id))
    except (ReportPeriod.DoesNotExist, ValueError):
        end_period = start_period

    periods = ReportPeriod.list_from_boundries(start_period, end_period)
#    periods=(start,end)
    
    if len(periods) > 1:
        dates = {'start': "%s, %s" % (periods[0].month,periods[0].year), 
                 'startgc': (periods[0].start_date), 
                 'end': "%s, %s" % (periods[len(periods)-1].month,periods[len(periods)-1].year),
                 'endgc': (periods[len(periods)-1].end_date)}
    elif len(periods) == 1:
        dates = {'start': "" , 
                 'end': "%s, %s" % (periods[0].month,periods[0].year),
                 'endgc': (periods[0].end_date)}
#        dates = {'start': start_period.month,
#                 'end': end_period.month}
        
#    if len(periods) == 1:
#        dates = {'start': periods[0].month, 'end': periods[0].month}
#    elif len(periods) > 1:
#        dates = {'start': periods.reverse()[0].month,
#                 'end': periods[0].month}

    grp = request.GET.get('grp')

    cls = Entry

    report_title = cls.TITLE
    rows = []
    count={}
    

    columns, sub_columns = cls.table_columns()
    if grp in ['region','woreda','zone']:
        
        #groups = []
        #for hp in scope.health_posts():HealthPost.objects.filter(type__name='region')
        #for hp in HealthPost.objects.filter(type__name=grp):
        #	groups.append(eval('hp.name'))
            #groups.append(eval('hp.%s' % grp))
        #groups = set(groups)
        #for group in HealthPost.objects.filter(type__name=grp):
        
        for group in scope.health_posts(type=grp):
            
            row = {}
            detail = []
            
            row['cells'] = []
            
            row['cells'].append({'value': unicode(group), 'id': '%s' % group.id})
            healthposts_group = HealthPost.objects.get(id=group.id)
            for hp in healthposts_group.descendants(include_self=False):
                detail.append(hp.name)
            results = (cls.aggregate_report(group, periods,scope.location))
            row['complete'] = results.pop('complete')
            
            for value in results.values():
                row['cells'].append({'value': value, 'num': True, 'detail': detail})
            
            rows.append(row)
            
        
        title = grp.title()
        columns.insert(0, {'name': title})
    else:
        for hp in scope.health_posts():
            row = {}
            row['cells'] = []
            row['cells'].append({'value': unicode(hp),
                                 'link': '/otp/health_post/%d' % hp.id,
                                 'id': '%s' % hp.id})
            results = cls.aggregate_report(hp, periods,scope.location)
            row['complete'] = results.pop('complete')
            for value in results.values():
                row['cells'].append({'value': value, 'num': True})
            rows.append(row)
        columns.insert(0, {'name': 'Health Post'})

    aocolumns_js = "{ \"sType\": \"html\" },"
    for col in columns[1:] + (sub_columns if sub_columns != None else []):
        if not 'colspan' in col:
            aocolumns_js += "{ \"asSorting\": [ \"desc\", \"asc\" ], " \
                            "\"bSearchable\": false },"
    aocolumns_js = aocolumns_js[:-1]

    if len(periods) > 1 or grp in ['woreda', 'region', 'zone']:
        aggregate = True
    else:
        aggregate = False
    print columns
    print sub_columns
    context_dict = {'get_vars': request.META['QUERY_STRING'], 'scope': scope,
                    'columns': columns, 'sub_columns': sub_columns,
                    'rows': rows, 'dates': dates, 'report_title': report_title,
                    'aggregate': aggregate, 'aocolumns_js': aocolumns_js,'webuser_location':scope.location,'healthposts' : scope.health_posts(type="woreda")}
    
    
    if request.GET.has_key('excel'):
        # lets take the model name as report title

                       
        #report_title = model_name = request.GET['model']

        #start, end = current_reporting_period()
        #month, year, late , dates_gc = current_reporting_period()
        #dates = {"start":start, "end":end}

        #table = create_table(request,model_name, scope)
        
        
        context_dict = {'model_name':model_name,
                        'dates': dates_GC,
                        'report_title':report_title,
                        'get_vars': request.META['QUERY_STRING'],
                        'columns':columns,
                        'sub_columns':sub_columns,
                        'rows':rows,
                        'aocolumns_js':aocolumns_js,
                        }
        
        
        response = HttpResponse(mimetype="application/vnd.ms-excel")
        filename = "%s %s.xls" % \
           (report_title, datetime.now().strftime("%d%m%Y"))
        response['Content-Disposition'] = "attachment; " \
                          "filename=\"%s\"" % filename
        response.write(create_excel(context_dict))
        return response

#    if request.method == 'GET' and 'excel' in request.GET:
#        response = HttpResponse(mimetype="application/vnd.ms-excel")
#        filename = "%s %s.xls" % \
#                   (report_title, datetime.now().strftime("%d%m%Y"))
#        response['Content-Disposition'] = "attachment; " \
#                                          "filename=\"%s\"" % filename
#        response.write(create_excel(context_dict))
#        return response
    else:
        return render_to_response('otp/report.html', context_dict, context_instance=RequestContext(request))


@login_required
@define_scope
def reporters_view(request,scope):
    ''' Displays a list of reporters '''
    
    reporters = scope.otp_reporters()
    
    table = None
    all = []
    for reporter in reporters:
    	rep = {}
    	rep['pk'] = reporter.id
    	rep['alias'] = reporter.user_name
    	rep['name'] = "%s %s %s (%s)" %(reporter.first_name, reporter.last_name, reporter.grandfather_name, reporter.user_name)
    	rep['hp'] = reporter.place_assigned #unicode(HealthPost.by_location(reporter.location))
    	rep['hp_pk'] = reporter.place_assigned.id # HealthPost.by_location(reporter.location).pk
    	#if reporter.connection():
    	rep['contact'] = reporter.phone
    	#rep['contact'] = reporter.connection().identity
    	#else:
    	#    rep['contact'] = ''
    	all.append(rep)
    	table = HealthWorkersTable(all, order_by=request.GET.get('sort'))
    return render_to_response('otp/health_workers.html', {"table": table, 'webuser_location':scope.location },context_instance=RequestContext(request))
    #return render_to_response('otp/health_workers.html', {"table": table },context_instance=RequestContext(request))



@csrf_protect
@login_required
@define_scope
def reporter(request, scope, reporter_id):
    ''' Display detail information about the reporter '''
    
    webuser = WebUser.by_user(request.user)
    webuser_location = webuser.location
    
    otp_reporter = OTPReporter.objects.get(id = reporter_id)
    reporter_detail = {}
    
    first_name = otp_reporter.first_name
    father_name = otp_reporter.last_name
    grandfather_name = otp_reporter.grandfather_name
    username = otp_reporter.user_name
    location = otp_reporter.place_assigned
    phone = otp_reporter.phone
    email = otp_reporter.email
    
    reporter_detail = {'first_name':first_name, 'father_name':father_name,'grandfather_name':grandfather_name,
                       'username':username, 'location':location, 'phone':phone, 'email':email}
    
    entries = scope.entries()
    # filter entries of the reporter
    entries = filter(lambda entries: entries.otp_reporter == otp_reporter, entries)
    
    # filter alerts of the reporter
    alerts = scope.alerts()
    alerts = filter(lambda alerts: alerts.otp_reporter == otp_reporter, alerts)
    
        
    all = []
    for otp_entry in entries:
        entry = SortedDict()
        entry['period'] = otp_entry.report_period
        entry['new_admission'] = otp_entry.new_admission
        entry['cured'] = otp_entry.cured
        entry['died'] = otp_entry.died
        entry['defaulted'] = otp_entry.defaulted
        entry['non_responded'] = otp_entry.non_responded
        entry['medical_transfer'] = otp_entry.medical_transfer
        entry['tfp_transfer'] = otp_entry.tfp_transfer   
        all.append(entry)
    table = ReporterEntryTable(all, order_by=request.GET.get('sort'))
    entry_rows = table.rows
    
    paginator = Paginator(entry_rows, 10)
    
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    
    try:
        entry_rows =  paginator.page(page)
    except (InvalidPage, EmptyPage):
        entry_rows = paginator.page(paginator.num_pages)
          
    reporter_detail['entry_rows'] = entry_rows
    reporter_detail['table'] = table
    
    all_alerts = []
    for otp_alert in alerts:
        alert = SortedDict()
        alert['notice'] = otp_alert.notice
        alert['time'] = otp_alert.time
        alert['resolved'] = otp_alert.resolved
        all_alerts.append(alert)
    
    alert_table = AlertTable(all_alerts, order_by=request.GET.get('sort'))
    alert_rows = alert_table.rows
    print "type %s" % type(alert_rows)
    
    
    
    paginator = Paginator(alert_rows, 10)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        alert_rows =  paginator.page(page)
    except (InvalidPage, EmptyPage):
        alert_rows = paginator.page(paginator.num_pages)
    
   
    
    
    
    
    
    reporter_detail['alert_rows'] = alert_rows
    reporter_detail['alert_table'] = alert_table
    print reporter_detail
    print "*********************"
    # add webuser location
    reporter_detail['webuser_location'] = webuser_location
    
    
    return render_to_response('otp/reporter.html',
                              reporter_detail,context_instance=RequestContext(request))

@login_required
@define_scope
def healthposts_view(request,scope):
    ''' Displays a list of reporters '''
    
    
    
    type=request.GET.get('filter')
    
    if type=='late':
        healthposts = HealthPost.get_late_healthposts(scope=scope, currnet_period = get_or_generate_reporting_period())
        label = "Late Health Post"
    elif type == 'completed':
        healthposts = HealthPost.get_completed_healthposts(scope, get_or_generate_reporting_period())
        label = "Completed Health Post"
    else:
        healthposts = scope.health_posts()
        label = "Health Posts"
    
    
    
    if healthposts:
        all = []
        for healthpost in healthposts:
            hp = {}
            hp['pk'] = healthpost.pk
            #hp['code'] = healthpost.code
            hp['name'] = "%s (%s)" %(healthpost.name,healthpost.code)
            hp['woreda'] = healthpost.parent
            rep = []
            for reporters in healthpost.reporters:
                rep.append(reporters.first_name)                
            hp['reporters'] = ", ".join(rep)
            hp['last_report'] = healthpost.last_report
            #take this code to properties...
            
            all.append(hp)
            table = HealthPostsTable(all, order_by=request.GET.get('sort'))
        return render_to_response('otp/health_posts.html', {"table": table, 'label':label, 'webuser_location':scope.location },context_instance=RequestContext(request))
    else:
	   return render_to_response('otp/health_posts.html', {'label':label,'webuser_location':scope.location},context_instance=RequestContext(request))

@login_required
@define_scope
def healthpost_view(request,scope, healthpost_id):
    ''' Displays a summary of location activities and history '''
    health_post = HealthPost.objects.get(id=healthpost_id)
    health_post_name = health_post.name
    health_post_type = health_post.type
    reporters= []
    for reporter in health_post.reporters:
        reporters.append({'name':'%s %s' %(reporter.first_name,reporter.last_name),
                          'phone':reporter.phone,
                          'is_active':reporter.is_active_reporter})
    
    entries = scope.entries()
    # filter entries of the reporter
    entries = filter(lambda entries: entries.health_post == health_post, entries)
    all = []
    for otp_entry in entries:
        entry = SortedDict()
        entry['period'] = otp_entry.report_period
        entry['new_admission'] = otp_entry.new_admission
        entry['cured'] = otp_entry.cured
        entry['died'] = otp_entry.died
        entry['defaulted'] = otp_entry.defaulted
        entry['non_responded'] = otp_entry.non_responded
        entry['medical_transfer'] = otp_entry.medical_transfer
        entry['tfp_transfer'] = otp_entry.tfp_transfer
        entry['otp_reporter'] = "%s %s" %(otp_entry.otp_reporter.first_name, otp_entry.otp_reporter.last_name)
        all.append(entry)
    table = HealthPostEntryTable(all, order_by=request.GET.get('sort'))
    entry_rows = table.rows
    
    paginator = Paginator(entry_rows, 10)
    
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    
    try:
        entry_rows =  paginator.page(page)
    except (InvalidPage, EmptyPage):
        entry_rows = paginator.page(paginator.num_pages)
            
    healthpost_detail = {'health_post': health_post,
                         'reporters':reporters,
                         'table':table , 'entry_rows':entry_rows}
            
    return render_to_response('otp/health_post.html',healthpost_detail,context_instance=RequestContext(request))




#Charts for OTP
@csrf_exempt
@login_required
@define_scope
def charts(request, scope):
#        ''' Display reported entries in chart form '''
#
#        webuser = WebUser.by_user(request.user)
#        webuser_descendent_locations = webuser.location.descendants(include_self = True)
#        descendent_location_types = set()
#        for location in webuser_descendent_locations: descendent_location_types.add(location.type.name)
#        # By default the chart is created for all
#        # periods, so get the periods and their id
#        report_periods = ReportPeriod.objects.all().order_by("id")
#        #period_start_id = report_periods[0].id
#        #period_end_id = report_periods[len(report_periods) -1 ].id
#        entries = scope.entries()
    ''' Display reported entries in chart form '''
    
    webuser = WebUser.by_user(request.user)
    webuser_location = webuser.location
    if webuser_location is not None:
        webuser_descendent_locations = webuser_location.descendants(include_self = True)
    descendent_location_types = set()
    for location in webuser_descendent_locations: descendent_location_types.add(location.type.name)
    
    
    # By default the chart is created for all
    # periods, so get the periods and their id
    
    report_periods = ReportPeriod.objects.all().order_by("id")
    #period_start_id = report_periods[0].id
    #period_end_id = report_periods[len(report_periods) -1 ].id
    #location_type_name = None
    entries = scope.entries()
    try:
        if webuser.location.type.name == "federal":
            entries_ = filter(lambda entries: entries.confirmed_by_region==True, entries)
           
        elif webuser.location.type.name == "region":
            entries_ = filter(lambda entries: entries.confirmed_by_zone==True, entries)
        elif webuser.location.type.name == "zone":
            entries_ = filter(lambda entries: entries.confirmed_by_woreda==True, entries)
            
        else:
            entries_ = entries
           #pass
        entries = entries_
    except:
        entries =  None
     # Get the filter parameter
    chart_src_path = None
    chart_src_path2 = None
    chart_src_path3 = None
    chart_src_path4 = None
    chart_src_path5 = None
    
    location_name = ""
    location_type = ""
    startmonth_id = ""
    endmonth_id = ""
        
    if request.method == "POST" and entries is not None:
        location_name = request.POST['location_name']
        location_type = request.POST['location_type']
        startmonth_id = request.POST['startmonth_id']
        endmonth_id = request.POST['endmonth_id']
        
    
        # both parameters are give, filter the data based on the values

        if location_name != "" and location_type != "":
            # Find location and desendents within the specified location
            location = HealthPost.objects.filter(name = location_name, type__name = location_type)[0]
            locations = location.descendants(include_self = True)
            #entry_ids = [entry.supply_place.location.location_ptr_id for entry in entries]
            location_id = [location.id for location in locations]
            entries = filter(lambda entries:
                           entries.health_post.id in location_id,entries)
            

        # if time range is given, filter the entries based on the range
        if startmonth_id != "":
            # Get the period range from the given date from ReportPeriod
            startmonth_start_date = ReportPeriod.objects.filter(id = startmonth_id)[0].start_date
            
            if endmonth_id != "":
                #endmonth_start_date = ReportPeriod.objects.filter(id = endmonth_id)[0].start_date
                endmonth_end_date = ReportPeriod.objects.filter(id = endmonth_id)[0].end_date
                report_periods = filter(lambda report_periods:
                                        report_periods.id >= int(startmonth_id) and
                                        report_periods.id <= int(endmonth_id), report_periods)
               
##                                entries = filter(lambda entries: startmonth_start_date <= entries.time and
##                                                 entries.time <= endmonth_end_date, entries)
                entries = filter(lambda entries: int(startmonth_id) <= entries.report_period.id and
                                 entries.report_period.id <= int(endmonth_id), entries)
                    
            else:
                startmonth_end_date = ReportPeriod.objects.filter(id = startmonth_id)[0].end_date
                report_periods = filter(lambda report_periods:
                                        report_periods.id == int(startmonth_id), report_periods)
##                                entries = filter(lambda entries: startmonth_start_date <= entries.time and
##                                                 entries.time <= startmonth_end_date , entries)
                entries = filter(lambda entries: entries.report_period.id == int(startmonth_id) , entries)
                
    # location information
    if location_type != "" and location_name != "":
        location_type_name = "%s %s" % (location_name, location_type)
    else:
        location_type_name = "%s %s" % (webuser_location.name, webuser_location.type.name)
                            
    # month-year as x-axis label
    months = ["%s \n %s" % (report_period.month, report_period.year)
        for report_period in report_periods]
    
    month_ids = [report_period.id  for report_period in report_periods]
    
    
    if entries is not None:
        #print "Has Entries under %s - %s" % (scope.location, entries[0].cured)
        
        admission_rate = []
        discharge_rate = []
        recovered_rate = []
        death_rate=[]
        defaulted_rate=[]
        non_responed_rate=[]
        transfer_tfp_rate = []
        
        
    #        total_balance = []
    #        total_admission = []
        for month_id in month_ids:
            total_admission_per_period = 0
            total_discharge_per_period = 0
            total_recovered_per_period = 0
            total_death_per_period = 0
            total_defaulted_per_period = 0
            total_non_responed_per_period = 0
            total_transfer_tfp_per_period = 0
            for entry in entries:
                #print entry.new_admission
                if entry.report_period.id == month_id:
                    #print entry.new_admission
                    total_admission_per_period += entry.new_admission
                    total_discharge_per_period += (entry.cured +
                                                   entry.died +
                                                   entry.defaulted +
                                                   entry.medical_transfer +
                                                   entry.non_responded +
                                                   entry.tfp_transfer)
                    total_recovered_per_period += entry.cured
                    total_death_per_period += entry.died
                    total_defaulted_per_period += entry.defaulted
                    total_non_responed_per_period += entry.non_responded
                    total_transfer_tfp_per_period += entry.tfp_transfer
                            
            
    #            total_discharge.append(total_discharge_per_period)
            if total_discharge_per_period > 0:
                recovered_rate.append((float(total_recovered_per_period)/total_discharge_per_period)*100)
                death_rate.append((float(total_death_per_period)/total_discharge_per_period)*100)
                defaulted_rate.append((float(total_defaulted_per_period)/total_discharge_per_period)*100)
                non_responed_rate.append((float(total_non_responed_per_period)/total_discharge_per_period)*100)
                transfer_tfp_rate.append((float(total_transfer_tfp_per_period)/total_discharge_per_period)*100)
            else:
                recovered_rate.append(0)
                death_rate.append(0)
                defaulted_rate.append(0)
                non_responed_rate.append(0)
                transfer_tfp_rate.append(0)
                
            
    #        print " new total recovered per period / Discharge is  ---> %s" % ((float(total_recovered_per_period)/total_discharge_per_period)*100)
        
        #figure = Figure()
        #canvas = FigureCanvas(figure)
        #plt = figure.add_subplot(111)
    #    print recovered_rate
        plt.figure(figsize=(4.5,4.5), dpi = 100)
        plt.plot(month_ids,recovered_rate, label = "Recovery Rate")
        
        plt.grid(True)
        plt.xlabel('Month')
        plt.ylabel('Rate')
        plt.xticks(month_ids, months, rotation = 45)
        plt.legend(loc="upper right")
    
    
        file_name = "otpet_chart_by_%s.png" % (webuser.id)
        chart_path = "otpet/static/graphs/%s" % file_name
        #chart_path =  file_name
        chart_src_path = "/static/otpet/graphs/%s" % file_name
            
        plt.savefig(chart_path)
        plt.close()
        
        plt.figure(figsize=(4.5,4.5), dpi = 100)
        plt.plot(month_ids,death_rate, label = "Death Rate")
        
        plt.grid(True)
        plt.xlabel('Month')
        plt.ylabel('Rate')
        plt.xticks(month_ids, months, rotation = 45)
        plt.legend(loc="upper right")
    
    
        file_name = "death_otpet_chart_by_%s.png" % (webuser.id)
        chart_path = "otpet/static/graphs/%s" % file_name
        #chart_path =  file_name
        chart_src_path2 = "/static/otpet/graphs/%s" % file_name
            
        plt.savefig(chart_path)
        plt.close()
        
        
        
        plt.figure(figsize=(4.5,4.5), dpi = 100)
        plt.plot(month_ids,defaulted_rate, label = "Defaulter Rate")

        
        plt.grid(True)
        plt.xlabel('Month')
        plt.ylabel('Rate')
        plt.xticks(month_ids, months, rotation = 45)
        plt.legend(loc="upper right")
    
    
        file_name = "nonresp_otpet_chart_by_%s.png" % (webuser.id)
        chart_path = "otpet/static/graphs/%s" % file_name
        #chart_path =  file_name
        chart_src_path4 = "/static/otpet/graphs/%s" % file_name
            
        plt.savefig(chart_path)
        plt.close()
        
        plt.figure(figsize=(4.5,4.5), dpi = 100)
        plt.plot(month_ids,non_responed_rate, label = "Non Responder Rate")
       
        plt.grid(True)
        plt.xlabel('Month')
        plt.ylabel('Rate')
        plt.xticks(month_ids, months, rotation = 45)
        plt.legend(loc="upper right")
    
    
        file_name = "tfp_otpet_chart_by_%s.png" % (webuser.id)
        chart_path = "otpet/static/graphs/%s" % file_name
        #chart_path =  file_name
        chart_src_path5 = "/static/otpet/graphs/%s" % file_name
            
        plt.savefig(chart_path)
        plt.close()
        
        plt.figure(figsize=(4.5,4.5), dpi = 100)
        plt.plot(month_ids,transfer_tfp_rate, label = "Transfer Out Rate") 
        
        plt.grid(True)
        plt.xlabel('Month')
        plt.ylabel('Rate')
        plt.xticks(month_ids, months, rotation = 45)
        plt.legend(loc="upper right")
    
    
        file_name = "defaulted_otpet_chart_by_%s.png" % (webuser.id)
        chart_path = "otpet/static/graphs/%s" % file_name
        #chart_path =  file_name
        chart_src_path3 = "/static/otpet/graphs/%s" % file_name
            
        plt.savefig(chart_path)
        plt.close()
    
    
    return render_to_response('otp/charts.html',
                                      {'chart_src_path': chart_src_path,
                                       'chart_src_path2': chart_src_path2,
                                       'chart_src_path3': chart_src_path3,
                                       'chart_src_path4': chart_src_path4,
                                       'chart_src_path5': chart_src_path5,
                                       'entries':entries,
                                       'descendent_locations': webuser_descendent_locations,
                                       'location_types': descendent_location_types,
                                       'location':location_type_name,
                                       'periods':ReportPeriod.objects.all().order_by("id"),
                                       'webuser_location':webuser_location},
                                      context_instance=RequestContext(request))

@csrf_exempt
@login_required
@define_scope
def send_sms(request, scope, reporter_id = None):

        if request.method == "POST":
                
                sms_text = request.POST['text_message'].replace('\n', '')
                #phone_numbers = request.POST['phone_number_list'].split(";")
                recipients = []
                reporters = scope.otp_reporters()
                for reporter in reporters:
                        if request.POST.has_key("reporter-id-" + str(reporter.pk)):
                                recipients.append(reporter)

                # create a temporary connection object for the phone number lists
                

##                print "*************** send Sms ***********"
##                print sms_text
##                print phone_numbers
##                print recipients
                                
                
                (message, reporter_received, reporter_not_received) = send_text_message(recipients, sms_text)
                
                        
        columns, sub_columns = OTPReporter.table_columns()
        rows = []
        results = OTPReporter.aggregate_report(scope = scope)
        
        for result in results:
                row = {}
                row['reporter_id'] = reporter_id = result.pop('reporter_id')
                # filter reporters who phone number
                reporter = OTPReporter.objects.get(id = reporter_id)
                if reporter.phone is not None:
                        row['cells'] = []
                        row['complete'] = True
                        for value in result.values():
                                row['cells'].append({'value':value})
                        rows.append(row)                

        aocolumns_js = "{ \"sType\": \"html\" },"
        for col in columns[1:]:
                if not 'colspan' in col:
                        aocolumns_js += "{ \"asSorting\": [ \"desc\", \"asc\" ], " \
                                    "\"bSearchable\": true },"
        aocolumns_js = aocolumns_js[:-1]
        
        
        return render_to_response('otp/send_sms.html',
                                  {'columns':columns,
                                   'sub_columns':sub_columns,
                                   'rows':rows,
                                   'aocolumns_js':aocolumns_js},
                                   context_instance=RequestContext(request))
            

	


