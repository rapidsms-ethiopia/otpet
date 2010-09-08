#!/usr/bin/env python
# vim: noet

from django.contrib.auth.decorators import login_required

from datetime import datetime, timedelta
import fpformat
import os
import sys
import math

from pygooglechart import SimpleLineChart, Axis, PieChart2D, StackedVerticalBarChart

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



##def send_sms(request):
##	if request.method != 'POST':
##        	raise Http404()
##	#sms_text = request.POST['sms_text'].replace('\r', '')
##	sms_text = request.POST['message'].replace('\r', '')
##	recipients = []
##    	for m in Monitor.objects.all():
##		if request.POST.has_key("monitor-" + str(m.pk)):
##			recipients.append(get_object_or_404(Monitor, pk=request.POST["monitor-" + str(m.pk)]))
##	
##	return HttpResponse(blast(recipients, sms_text), mimetype="text/plain")

def simple(request):
    import random
    
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter
    
    

    fig=Figure()
    ax=fig.add_subplot(111)
    x=[]
    x1=[]
    x2=[]
    x3=[]
    x4=[]
    x5=[]
    y=[]
    y1=[]
    y2=[]
    y3=[]
    y4=[]
    y5=[]
    
    now=datetime.now()
    delta=timedelta(days=7)
    for i in range(13):
        x.append(now)
        x1.append(now)
        x2.append(now)
        x3.append(now)
        x4.append(now)
        x5.append(now)
        now+=delta
        y.append(random.randint(0, 1000))
        y1.append(random.randint(0, 1000))
        y2.append(random.randint(0, 1000))
        y3.append(random.randint(0, 1000))
        y4.append(random.randint(0, 1000))
        y5.append(random.randint(0, 1000))
        
    ax.plot_date(x1, y1,'-')
    ax.plot_date(x, y,'-')
    ax.plot_date(x2, y2,'-')
    ax.plot_date(x3, y3,'-')
    ax.plot_date(x4, y4,'-')
    ax.plot_date(x5, y5,'-')
    
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    canvas=FigureCanvas(fig)
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


@login_required
@define_scope
def hp_chart(request, scope, healthpostid):
    
    import random
    
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter
    
    

    fig=Figure()
    ax=fig.add_subplot(111)
    
    
    
    
    
    #set initial...
   
        
    
    
    
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

#    periods = ReportPeriod.list_from_boundries(start_period, end_period)
    periods = ReportPeriod.objects.all().order_by('id')
    
#    if len(periods) == 1:
#        dates = {'start': periods[0].start_date, 'end': periods[0].end_date}
#        start_date = periods[0].start_date
#    elif len(periods) > 1:
#        dates = {'start': periods.reverse()[0].start_date,
#                 'end': periods[0].end_date}
#        start_date = periods.reverse()[0].start_date

    grp = request.GET.get('grp')
    healthpost_id = healthpostid
    cls = Entry

    report_title = cls.TITLE
    rows = []
    count={}
    

    now=start_date #datetime.now()
    x=[]
    nadm = []
    cured = []
    died = []
    defaulted = []
    nresp = []
    medt = []
    tfpt = []
    
           
    
    for i in range(len(periods)):
#        x.append(start_date)
        x.append(periods.reverse()[i].start_date)
        #x2.append(periods.reverse()[i].start_date)
        results = cls.aggregate_chart(HealthPost.objects.get(id=healthpost_id),periods[i])
        nadm.append(results['nadm'])
        cured.append(results['cured'])
        died.append(results['died'])
        defaulted.append(results['defaulted'])
        nresp.append(results['nresp'])
        medt.append(results['medt'])
        tfpt.append(results['tfpt'])
#        row['complete'] = results.pop('complete')
#        for value in results.values():
#            row['cells'].append({'value':value})
#        rows.append(row)
#        y.append(random.randint(0, 1000))
        
#        y.append(rows[0]['cells'][0]['value'])
#        y.append(i+1)
    #ax.axis(ymin=0)
        
    ax.plot_date(x, nadm, '-', label="New Admission")
    ax.plot_date(x, cured, '-')
    ax.plot_date(x, died, '-')
    ax.plot_date(x, defaulted, '-')
    ax.plot_date(x, nresp, '-')
    ax.plot_date(x, medt, '-')
    ax.plot_date(x, tfpt, '-')
    ax.grid(True)
    ax.legend()
#    ax.axvline(ymin=0)
#    ax.axis([ymin=0])
   
    ax.xaxis.set_major_formatter(DateFormatter('%d-%m-%Y'))
    fig.autofmt_xdate()
    canvas=FigureCanvas(fig)
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response



@login_required
@define_scope
def report_chart(request, scope):
    
    import random
    
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter
    
    

    fig=Figure()
    ax=fig.add_subplot(111)
    
    
    
    
    
    #set initial...
   
        
    
    
    
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
    
    if len(periods) == 1:
        dates = {'start': periods[0].start_date, 'end': periods[0].end_date}
        start_date = periods[0].start_date
    elif len(periods) > 1:
        dates = {'start': periods.reverse()[0].start_date,
                 'end': periods[0].end_date}
        start_date = periods.reverse()[0].start_date

    grp = request.GET.get('grp')
    healthpost_id = request.GET.get('hp')

    cls = Entry

    report_title = cls.TITLE
    rows = []
    count={}
    

    now=start_date #datetime.now()
    x=[]
    nadm = []
    cured = []
    died = []
    defaulted = []
    nresp = []
    medt = []
    tfpt = []
    
           
    
    for i in range(len(periods)):
#        x.append(start_date)
        x.append(periods.reverse()[i].start_date)
        #x2.append(periods.reverse()[i].start_date)
        results = cls.aggregate_chart(HealthPost.objects.get(id=healthpost_id),periods[i])
        nadm.append(results['nadm'])
        cured.append(results['cured'])
        died.append(results['died'])
        defaulted.append(results['defaulted'])
        nresp.append(results['nresp'])
        medt.append(results['medt'])
        tfpt.append(results['tfpt'])
#        row['complete'] = results.pop('complete')
#        for value in results.values():
#            row['cells'].append({'value':value})
#        rows.append(row)
#        y.append(random.randint(0, 1000))
        
#        y.append(rows[0]['cells'][0]['value'])
#        y.append(i+1)
    #ax.axis(ymin=0)
        
    ax.plot_date(x, nadm, '-', label="New Admission")
    ax.plot_date(x, cured, '-')
    ax.plot_date(x, died, '-')
    ax.plot_date(x, defaulted, '-')
    ax.plot_date(x, nresp, '-')
    ax.plot_date(x, medt, '-')
    ax.plot_date(x, tfpt, '-')
    ax.grid(True)
    ax.legend()
#    ax.axvline(ymin=0)
#    ax.axis([ymin=0])
   
    ax.xaxis.set_major_formatter(DateFormatter('%d-%m-%Y'))
    fig.autofmt_xdate()
    canvas=FigureCanvas(fig)
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response

    
@login_required
@define_scope
def reports_pie(request,scope):
   
#    fig=Figure()
#    #plt.figure(figsize=(3,3))
#    x = [6,6]
#    labels = ['Complete', 'incomplete']
#    ax=fig.add_subplot(111)
#    ax.pie(x,labels=labels)
#    canvas=FigureCanvas(fig)
#    response=HttpResponse(content_type='image/png')
#    canvas.print_png(response)
#    return response

    from pylab import *
    #import random
    
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    #from matplotlib.dates import DateFormatter
    
    
    if datetime.today().weekday() == 6:
        period = ReportPeriod.objects.latest()
    else:
        period = ReportPeriod.from_day(datetime.today())
        #period = ReportPeriod.weekboundaries_from_day(datetime.today())
    
    #summary['periodid'] = ReportPeriod.weekboundaries_from_day(datetime.today()).id
    #healthposts = len(scope.health_posts())
    completed = len(scope.current_entries())
    incomplete = len(scope.health_posts()) - len(scope.current_entries())
    #summary['percent'] = round(float(len(scope.current_entries())) / float(len(scope.health_posts())) * 100.0)
    #summary['up2date'] = len(filter(lambda hc: hc.up2date(),

    fig = Figure()
    ax=fig.add_subplot(111, axisbg='r')
    fig.set_figheight(2)
    fig.set_figwidth(2)
    fig.set_facecolor('w')
    #fig=figure(1, figuresize=(3,3))
    #ax = axes([0.2,0.2,0.8,0.8])
    labels = 'Completed', 'Incomlete'
    fracs = [completed,incomplete]
    explode=(0,0.01)
    pie(fracs, explode=explode, labels=None,colors=('g','r'), autopct='%1.1f%%', shadow=True)
    title('Reports..', bbox={'facecolor':'0.5', 'pad':5})
    ax.pie(fracs, explode=explode, labels=None,colors=('#52E060','#F7976E'), autopct='%1.1f%%', shadow=True)
    #ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    #fig.autofmt_xdate()
    canvas=FigureCanvas(fig)
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


@login_required
@define_scope
def index(request,scope):
    '''Display home page / Dashboard'''
    summary = {}
    if datetime.today().weekday() == 6:
        period = ReportPeriod.objects.latest()
    else:
        period = ReportPeriod.from_day(datetime.today())
        #period = ReportPeriod.weekboundaries_from_day(datetime.today())
    summary['period'] = period
    #summary['periodid'] = ReportPeriod.weekboundaries_from_day(datetime.today()).id
    summary['health_posts'] = len(scope.health_posts())
    summary['completed'] = len(scope.current_entries())
    summary['missing'] = len(scope.health_posts()) - len(scope.current_entries())
    try:
        summary['percent'] = round(float(len(scope.current_entries())) / float(len(scope.health_posts())) * 100.0)
    except:
        summary['percent'] = 0
    #summary['up2date'] = len(filter(lambda hc: hc.up2date(),
    #                                           scope.health_units()))
    #summary['missing'] = summary['total_units'] - summary['up2date']

	
    entries = scope.current_entries()
	#Entry.objects.all()
    if entries:	
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
            all.append(ent)
            table = EntryTable(all, order_by=request.GET.get('sort'))
        return render_to_response('otp/index.html',{"ent" : ent, "summary" : summary, "table": table },context_instance=RequestContext(request))
    else:
        return render_to_response('otp/index.html',{"summary" : summary },context_instance=RequestContext(request))
	
	
@login_required
@define_scope
def charts_view(request, scope):
    ''' Show available reports '''

    return render_to_response('otp/otp_chart.html',
                              {'scope': scope,
                               'periods': ReportPeriod.objects.all()},
                               context_instance=RequestContext(request))
    	
	

    
@login_required
@define_scope
def chart_view(request, scope):
    ''' Show available reports '''

    return render_to_response('otp/chart.html',
                              {'scope': scope},
                               context_instance=RequestContext(request))
	
	
	
@login_required
@define_scope
def reports_view(request, scope):
    ''' Show available reports '''

    return render_to_response('otp/otp_reports.html',
                              {'scope': scope,
                               'periods': ReportPeriod.objects.all()},
                               context_instance=RequestContext(request))
    
    
    
@login_required
@define_scope
def report_view(request, scope):  
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
    
    if len(periods) == 1:
        dates = {'start': periods[0].start_date, 'end': periods[0].end_date}
    elif len(periods) > 1:
        dates = {'start': periods.reverse()[0].start_date,
                 'end': periods[0].end_date}

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
            
            row['cells'] = []
            row['cells'].append({'value': unicode(group)})
            results = (cls.aggregate_report(group, periods))
            row['complete'] = results.pop('complete')
            
            for value in results.values():
                row['cells'].append({'value': value, 'num': True})
            
            rows.append(row)
            
        
        title = grp.title()
        columns.insert(0, {'name': title})
    else:
        for hp in scope.health_posts():
            row = {}
            row['cells'] = []
            row['cells'].append({'value': unicode(hp),
                                 'link': '/otp/health_post/%d' % hp.id})
            results = cls.aggregate_report(hp, periods)
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
                    'aggregate': aggregate, 'aocolumns_js': aocolumns_js}

    if request.method == 'GET' and 'excel' in request.GET:
        response = HttpResponse(mimetype="application/vnd.ms-excel")
        filename = "%s %s.xls" % \
                   (report_title, datetime.now().strftime("%d%m%Y"))
        response['Content-Disposition'] = "attachment; " \
                                          "filename=\"%s\"" % filename
        response.write(create_excel(context_dict))
        return response
    else:
        return render_to_response('otp/report.html', context_dict, context_instance=RequestContext(request))


@login_required
@define_scope
def reporters_view(request,scope):
	''' Displays a list of reporters '''

	reporters = scope.otp_reporters()

	all = []
	for reporter in reporters:
		rep = {}
		rep['pk'] = reporter.pk
		rep['alias'] = reporter.alias
		rep['name'] = reporter.full_name().title()
		rep['hp'] = unicode(HealthPost.by_location(reporter.location))
		rep['hp_pk'] = HealthPost.by_location(reporter.location).pk
		#if reporter.connection():
		rep['contact'] = reporter.phone
		#rep['contact'] = reporter.connection().identity
		#else:
		#    rep['contact'] = ''
		all.append(rep)
		table = HealthWorkersTable(all, order_by=request.GET.get('sort'))
	return render_to_response('otp/health_workers.html', {"table": table },context_instance=RequestContext(request))
	#return render_to_response('otp/health_workers.html', {"table": table },context_instance=RequestContext(request))

@login_required
def reporter_view(request, reporter_id):
    ''' Displays a summary of his activities and history '''

    reporter = OTPReporter.objects.get(id=reporter_id)

    return render_to_response('otp/health_worker.html',
                              {"reporter": reporter},context_instance=RequestContext(request))

@login_required
@define_scope
def healthposts_view(request,scope):
	''' Displays a list of reporters '''

	healthposts = scope.health_posts()

	if healthposts:
		all = []
		for healthpost in healthposts:
			hp = {}
			hp['pk'] = healthpost.pk
			hp['code'] = healthpost.code
			hp['name'] = healthpost.name
			hp['woreda'] = healthpost.parent
			hp['zone'] = healthpost.parent.parent
			hp['region'] = healthpost.parent.parent.parent
			#take this code to properties...

			all.append(hp)
			table = HealthPostsTable(all, order_by=request.GET.get('sort'))
		return render_to_response('otp/health_posts.html', {"table": table },context_instance=RequestContext(request))
	else:
		return render_to_response('otp/health_posts.html', {},context_instance=RequestContext(request))

@login_required
def healthpost_view(request, healthpost_id):
    ''' Displays a summary of location activities and history '''
    health_post = HealthPost.objects.get(id=healthpost_id)
    reporters = OTPReporter.objects.filter(location=health_post.location_ptr)
    all = []
    for reporter in reporters:
        rep={}
        rep['alias'] = reporter.alias
        rep['name'] = reporter.full_name().title()
        all.append(rep)
        
    periods = ReportPeriod.objects.all().order_by('-end_date')
    
    columns = [{'name': 'Period'}, 
               #{'name': 'To'}, 
#               {'name': 'Begining Balance'}, 
#               {'name': 'New Admission'}, 
               {'name': 'New Admissions'}, 
               {'name': 'Cured'},
               {'name': 'Death'}, 
                {'name': 'Defaulter'}, 
                {'name': 'Non Respondents'}, 
                {'name': 'Medical Transfer'}, 
                {'name': 'Transfered to TFP'},
#                {'name': 'End Balance'}, 
               ]
    
    report = []
    
    for period in periods:
        row = {}
        row['cells'] = []
        row['cells'].append({'value': period.start_date, 'date' : True})#.strftime("%a")})
        
        #row['cells'].append({'value': period.end_date, 'date' : True})
        results = Entry.aggregate_healthpost(health_post,[period])
        row['complete'] = results.pop('complete')
        for value in results.values():
            row['cells'].append({'value':value, 'num':True})
        report.append(row)
        
    context_dict = {'health_post': health_post, 'report':report , 'columns':columns}
            
    
        
    return render_to_response('otp/health_post.html',context_dict,context_instance=RequestContext(request))




def to_print(request, app_label, model_name):
	data = []
	
	# only OTPs are supported right now
	if app_label != "inventory"\
	or model_name != "location":
		raise http.Http404(
		"App %r, model %r, not supported."\
		% (app_label, model_name))
	
	# collate regions as top-level sections
	for region in Region.objects.all().order_by('name'):
		zones = region.zone_set.all().order_by('name')
		for zone in zones:
			
			# collate OTPs by woreda, and perform
			# magic to make a four-column table 
			# using django's crappy templates
			areas = zone.area_set.all().order_by('name')
			for area in areas:
				locations = area.location_set.all().order_by('name')
		
				n = 0
				for location in locations:
					setattr(location, "left", (n+1) % 2)
					setattr(location, "right", n % 2)
					n += 1
		
				# list all OTPs per woreda
				setattr(area, "locations", locations)
			setattr(zone, "areas", areas)
		setattr(region, "zones", zones)
		data.append(region)
	
	return render_to_response(request,"reference.html", {"regions": data})

def refresh_graphs():
	print graph_entries()
	print graph_otps()
	print graph_monitors()
	print graph_avg_stat()

	return 'refreshed graphs'

def graph_entries(num_days=14):
	# its a beautiful day
	today = datetime.today().date()

	# step for x axis
	step = timedelta(days=1)

	# empties to fill up with data
	counts = []
	dates = []

	# only get last two weeks of entries 
	day_range = timedelta(days=num_days)
	entries = Entry.objects.filter(
			time__gt=(today	- day_range))
	
	# count entries per day
	for day in range(num_days):
		count = 0
		d = today - (step * day)
		for e in entries:
			if e.time.day == d.day:
				count += 1
		dates.append(d.day)
		counts.append(count)
    
    	line = SimpleLineChart(440, 100, y_range=(0, 100))
	line.add_data(counts)
	line.set_axis_labels(Axis.BOTTOM, dates)
	line.set_axis_labels(Axis.BOTTOM, ['','Date', ''])
	line.set_axis_labels(Axis.LEFT, ['', 50, 100])
	line.set_colours(['0091C7'])
	line.download('apps/RUTF/graphs/entries.png')
	
	return 'saved entries.png' 


def graph_monitors(num_days=14):
	# pie chart of monitors
	day_range = timedelta(days=num_days)
	reported = 0
	mons = Monitor.objects.all()
	for m in mons:
		if m.latest_report != 'N/A':
			if m.latest_report.time.date() > (datetime.today().date() - day_range):
				reported += 1

	chart = PieChart2D(275, 60)
	chart.add_data([(len(mons)-reported), reported])
	#chart.set_pie_labels(['', 'Reporting Monitors'])
	chart.set_legend(['Non-reporting Monitors', 'Reporting Monitors'])
	chart.set_colours(['0091C7','0FBBD0'])
	chart.download('apps/RUTF/graphs/monitors.png')

	return 'saved monitors.png' 
	

def graph_otps():
	# pie chart of otps
	ent = Entry.objects.all()
	visited = 0
	for e in ent:
		if e.supply_place.type == 'OTP':
			visited += 1

	otps = len(Location.objects.all())
	percent_visited = float(visited)/float(otps)
	percent_not_visited = float(otps - visited)/float(otps)

	chart = PieChart2D(275, 60)
	chart.add_data([(percent_not_visited*100), (percent_visited*100)])
	#chart.set_pie_labels(['', 'Visited OTPs'])
	chart.set_legend(['Non-visited OTPs', 'Visited OTPs'])
	chart.set_colours(['0091C7','0FBBD0'])
	chart.download('apps/RUTF/graphs/otps.png')

	return 'saved otps.png' 
	

def graph_avg_stat():	
	# bar chart of avg wor and otp stats	
	# and pie chart of avg otp coverage

	# lots of variables
	# for summing all these data
	# o_num => number of otps
	# w_q => woreda quantity
	# etc
	o_num = 0
	o_b = 0
	o_q = 0
	o_c = 0
	o_s = 0

	w_num = 0
	w_b = 0
	w_q = 0
	w_c = 0
	w_s = 0

	# in first pass we're gathering
	# a list of woredas that have been
	# visited, along with summing all
	# their data
	woreda_list = []

	ent = Entry.objects.all()

	for e in ent:
		if e.supply_place.type == 'Woreda':
			w_num += 1
			#if e.beneficiaries is not None:
				#w_b += e.beneficiaries
			
			if e.quantity is not None:
				w_q += e.quantity
			if e.consumption is not None:
				w_c += e.consumption
			if e.balance is not None:
				w_s += e.balance
			woreda_list.append(e.supply_place.area)

	# this is obnoxious but the best
	# way python will allow making a
	# dict from a list
	woredas = { " " : 0}
	woredas = woredas.fromkeys(woreda_list, 0)

	# second pass to gather otp sums
	# why a second pass? bc we need to
	# add visted otp sums to the woreda dict 
	for e in ent:
		if e.supply_place.type == 'OTP':
			o_num += 1
			#if e.beneficiaries is not None:
				#o_b += e.beneficiaries
			if e.quantity is not None:
				o_q += e.quantity
			if e.consumption is not None:
				o_c += e.consumption
			if e.balance is not None:
				o_s += e.balance

			if e.supply_place.location.area in woredas:
				woredas[e.supply_place.location.area] += 1
	
	# make a list of tuples from dict
	# (woreda obj, num-of-its-otps-that-have-been-visited)
	woreda_list = woredas.items()

	# a for average otps visited
	a = 0

	# n for number of total otps in woreda
	n = 0

	# count total otps and compute average
	# and add this to the global sums
	for t in woreda_list:
		n += t[0].number_of_OTPs
		if t[1] != 0:
			a += float(t[0].number_of_OTPs)/float(t[1])
	
	# normalize for graphing
	d_a = float(a)/float(n)
	d_n = 1 - d_a

	# average otp and woreda data, 
	#o_b = (float(o_b)/float(o_num))
	o_q = (float(o_q)/float(o_num))
	o_c = (float(o_c)/float(o_num))
	o_s = (float(o_s)/float(o_num))
	#w_b = (float(w_b)/float(w_num))
	w_q = (float(w_q)/float(w_num))
	w_c = (float(w_c)/float(w_num))
	w_s = (float(w_s)/float(w_num))

	pie = PieChart2D(275, 60)
	pie.add_data([(d_n*100), (d_a*100)])
	#pie.set_pie_labels(['', 'Avg visited OTPs per woreda'])
	pie.set_legend(['Avg non-visted OTPs per woreda', 'Avg visited OTPs per woreda'])
	pie.set_colours(['0091C7','0FBBD0'])
	pie.download('apps/RUTF/graphs/avg_otps.png')

	bar = StackedVerticalBarChart(400,100)
	bar.set_colours(['4d89f9','c6d9fd'])
	bar.add_data([o_q, o_c, o_s])
	bar.add_data([w_q, w_c, w_s])
	bar.set_axis_labels(Axis.BOTTOM, ['Ben', 'Qty', 'Con', 'Bal'])
	bar.download('apps/RUTF/graphs/avg_stat.png')

	return 'saved avg_stat.png' 



@login_required
def register_hew(request):
        ''' It is used to register HEW from woreda level
        by the woreda health officer or system adminstrator'''

@login_required
@define_scope
def reports_test(request,scope):
        ''' Displays reports in a tabular form.
        the user can also filter reports'''
        ''' Displays reports in a tabular form.
        the user can also filter reports'''
        if request.method == "POST":
                filter_parameters = request.POST
                model_app_name = filter_parameters['model']
                app_label,model_name = model_app_name.split("-")
                base_model = models.get_model(app_label,model_name)
              
                base_dataset = base_model.objects.all()
                if model_name == "entry":
                        all = []
                        otp_entries = scope.entries()
                        for otp_entry in otp_entries:
                                entry = {}
                                entry['pk'] = otp_entry.pk
                                entry['otp_reporter'] = otp_entry.otp_reporter
                                entry['health_post'] = otp_entry.health_post
                                entry['hp_pk'] = otp_entry.health_post.pk
                                entry['new_admission'] = otp_entry.new_admission
                                entry['cured'] = otp_entry.cured
                                entry['died'] = otp_entry.died
                                entry['defaulted'] = otp_entry.defaulted
                                entry['non_responded'] = otp_entry.non_responded
                                entry['medical_transfer'] = otp_entry.medical_transfer
                                entry['tfp_transfer'] = otp_entry.tfp_transfer
                                entry['entry_time'] = otp_entry.entry_time
                                all.append(entry)
                        table = EntryTable(all, order_by=request.GET.get('sort'))
                elif model_name =="alert":
                        all = []
                        otp_alerts = scope.alerts()
                        for otp_alert in rutf_alerts:
                                alert = {}
                                alert['notice'] = otp_alert.notice
                                alert['resolved'] = otp_alert.resolved
                                alert['time'] = otp_alert.time
                                alert['otp_reporter'] = otp_alert.otp_reporter
                                all.append(alert)
                        table = AlertTable(all, order_by=request.GET.get('sort'))
                elif model_name =="otpreporter":
                        all = []
                        otp_reporters = scope.otp_reporters()                        
                        for otp_reporter in otp_reporters:
                                reporter = {}
                                reporter['pk'] = otp_reporter.pk
                                reporter['alias'] = otp_reporter.alias
                                reporter['name'] = otp_reporter.full_name().title()
                                reporter['hp'] = unicode(HealthPost.by_location(otp_reporter.location))
                                reporter['hp_pk'] = HealthPost.by_location(otp_reporter.location).pk
                                reporter['contact'] = otp_reporter.phone
                                all.append(reporter)
                        table = HealthWorkersTable(all, order_by=request.GET.get('sort'))

                elif model_name == "healthpost":
                        #all = []
                        #otp_healthposts = scope.health_posts()
                        #for otp_healthpost in otp_healthposts:
                                # To filter out only the health posts
                        #        if otp_healthpost.type.name == "health post":
                        #                health_post = {}
                        #                health_post['name'] = otp_healthpost.name
                        #                health_post['code'] = otp_healthpost.code
                        #                health_post['type'] = otp_healthpost.type.name
                        #                health_post['child_number'] = otp_healthpost.number_of_child_location
                        #                health_post['parent_name'] = otp_healthpost.parent_location_name
                        #                all.append(health_post)
                        #table = RepHealthPostTable(all, order_by=request.GET.get('sort'))
                        healthposts = scope.health_posts()

                        if healthposts:
                            all = []
                            for healthpost in healthposts:
                                hp = {}
                                hp['pk'] = healthpost.pk
                                hp['code'] = healthpost.code
                                hp['name'] = healthpost.name
                                hp['woreda'] = healthpost.parent
                                hp['zone'] = healthpost.parent.parent
                                hp['region'] = healthpost.parent.parent.parent
                                #take this code to properties...

                                all.append(hp)
                                table = HealthPostsTable(all, order_by=request.GET.get('sort'))               
                return render_to_response('otp/reports.html',
                                          {'model_name':model_name,'table':table},
                                          context_instance=RequestContext(request))
        else:
                # By default, the report page displays the previous entries
                model_name = 'entry'
                otp_entries = scope.entries()
                all = []
                for otp_entry in otp_entries:
                        entry = {}
                        entry['pk'] = otp_entry.pk
                        entry['otp_reporter'] = otp_entry.otp_reporter
                        entry['health_post'] = otp_entry.health_post
                        entry['hp_pk'] = otp_entry.health_post.pk
                        entry['new_admission'] = otp_entry.new_admission
                        entry['cured'] = otp_entry.cured
                        entry['died'] = otp_entry.died
                        entry['defaulted'] = otp_entry.defaulted
                        entry['non_responded'] = otp_entry.non_responded
                        entry['medical_transfer'] = otp_entry.medical_transfer
                        entry['tfp_transfer'] = otp_entry.tfp_transfer
                        entry['entry_time'] = otp_entry.entry_time
                        all.append(entry)
                table = EntryTable(all, order_by=request.GET.get('sort'))
                return render_to_response('otp/reports.html',
                                          {'model_name':model_name,'table':table},
                                          context_instance=RequestContext(request))


	


@login_required
def reports(request):
        ''' Displays reports in a tabular form.
        the user can also filter reports'''
        ''' Displays reports in a tabular form.
        the user can also filter reports'''
        if request.method == "POST":
                filter_parameters = request.POST
                model_app_name = filter_parameters['model']
                app_label,model_name = model_app_name.split("-")
                base_model = models.get_model(app_label,model_name)
              
                base_dataset = base_model.objects.all()
                if model_name == "entry":
                        all = []
                        rutf_entries = scope.entries()
                        for rutf_entry in rutf_entries:
                                entry = {}
                                entry['supply_place'] = rutf_entry.supply_place
                                entry['quantity'] = rutf_entry.quantity
                                entry['consumption'] = rutf_entry.consumption
                                entry['balance'] = rutf_entry.balance
                                entry['rutf_reporter'] = rutf_entry.rutf_reporter
                                all.append(entry)
                        table = EntryTable(all, order_by=request.GET.get('sort'))
                elif model_name =="alert":
                        all = []
                        rutf_alerts = scope.alerts()
                        for rutf_alert in rutf_alerts:
                                alert = {}
                                alert['notice'] = rutf_alert.notice
                                alert['resolved'] = rutf_alert.resolved
                                alert['time'] = rutf_alert.time
                                alert['rutf_reporter'] = rutf_alert.rutf_reporter
                                all.append(alert)
                        table = AlertTable(all, order_by=request.GET.get('sort'))
                elif model_name =="supply":
                        all = []
                        for rutf_supply in base_dataset:
                                supply = {}
                                supply['name'] = rutf_supply.name
                                supply['code'] = rutf_supply.code
                                supply['unit'] = rutf_supply.unit
                                all.append(supply)
                        table = SupplyTable(all, order_by=request.GET.get('sort'))
                elif model_name =="rutfreporter":
                        all = []
                        rutf_reporters = scope.rutf_reporters()                        
                        for rutf_reporter in rutf_reporters:
                                reporter = {}
                                reporter['first_name'] = rutf_reporter.first_name
                                reporter['last_name'] = rutf_reporter.last_name
                                reporter['phone'] = rutf_reporter.phone
                                reporter['location'] = rutf_reporter.location
                                all.append(reporter)
                        table = RUTFReporterTable(all, order_by=request.GET.get('sort'))

                elif model_name == "healthpost":
                        all = []
                        rutf_healthposts = scope.health_posts()
                        for rutf_healthpost in rutf_healthposts:
                                # To filter out only the health posts
                                if rutf_healthpost.type.name == "health post":
                                        health_post = {}
                                        health_post['name'] = rutf_healthpost.name
                                        health_post['code'] = rutf_healthpost.code
                                        health_post['type'] = rutf_healthpost.type.name
                                        health_post['child_number'] = rutf_healthpost.number_of_child_location
                                        health_post['parent_name'] = rutf_healthpost.parent_location_name
                                        all.append(health_post)
                        table = HealthPostTable(all, order_by=request.GET.get('sort'))
                
                return render_to_response('rutf/otp_reports.html',
                                          {'model_name':model_name,'table':table},
                                          context_instance=RequestContext(request))
        else:
                # By default, the report page displays the previous entries
                model_name = 'entry'
                rutf_entries = scope.entries()
                all = []
                for rutf_entry in rutf_entries:
                        entry = {}
                        entry['supply_place'] = rutf_entry.supply_place
                        entry['quantity'] = rutf_entry.quantity
                        entry['consumption'] = rutf_entry.consumption
                        entry['balance'] = rutf_entry.balance
                        entry['rutf_reporter'] = rutf_entry.rutf_reporter
                        all.append(entry)
                table = EntryTable(all, order_by=request.GET.get('sort'))
                return render_to_response('rutf/otp_reports.html',
                                          {'model_name':model_name,'table':table},
                                          context_instance=RequestContext(request))



@login_required
def charts(request):
        ''' Display reported entries in chart form '''


@login_required
def map_entries(request):
	def has_coords(entry):
		loc = entry.supply_place.location
		if loc is None: return False
		return  (loc.latitude is not None) and (loc.longitude is not None)
		
	entries = filter(has_coords, Entry.objects.all())
	#return render_to_response(request,"rutf/map.html", {"entries": entries})
	return render_to_response(request,"rutf/entries.html", {"entries": entries})
	


