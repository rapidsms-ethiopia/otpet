
from django.db import models
from django.contrib.auth import models as auth_models
from django.core.exceptions import ObjectDoesNotExist 

from datetime import date as pydate
from datetime import timedelta, datetime

from django.contrib.auth.models import User, UserManager
from django.contrib.auth.admin import UserAdmin 
from django.contrib.auth.forms import UserCreationForm 
from django.utils.datastructures import SortedDict

from locations.models import Location, LocationType

from django.db.models import Sum



from django.utils.translation import ugettext as _
from django.utils.datastructures import SortedDict

from rapidsms.models import Contact, Connection


class HealthPost(Location, models.Model):
    	class Meta:
            ordering = ["name"]      
    
        def __unicode__(self):
            return u'%s' % (self.name)
    
    	@classmethod
    	def by_location(cls, location):
            try:
                return cls.objects.get(location_ptr = location)
            except cls.DoesNotExist:
                return None
            
        @classmethod
        def get_completed_healthposts(cls, scope, current_period):
            entries = scope.entries()
            current_entries = filter(lambda entries:
                                              entries.report_period == current_period,
                                              entries)
            submitted_healthposts=[]
    
            locations = scope.health_posts()
            #filter locations which are health posts only
            health_posts = filter(lambda locations:
                                 locations.type.name.lower() == "health post",
                                 locations)
            
            #get health posts who has successfully sent their report.
            for entry in current_entries:
                    submitted_healthposts.append(entry.health_post)
            return submitted_healthposts
                        
        @classmethod
        def get_late_healthposts(cls,  current_period, scope=None):
            if scope is not None:
                entries = scope.entries()
                locations = scope.health_posts()
            else:
                entries = entries = Entry.objects.all()
                locations = HealthPost.objects.all()
            
            current_entries = filter(lambda entries:
                                              entries.report_period == current_period,
                                              entries)
            submitted_healthposts=[]
    
            
            #filter locations which are health posts only
            health_posts = filter(lambda locations:
                                 locations.type.name.lower() == "health post",
                                 locations)
            
            #get health posts who has successfully sent their report.
            for entry in current_entries:
                    submitted_healthposts.append(entry.health_post)
            
            #filter out the health posts who hasn't yet sent their report.  
            late_healthpost = filter(lambda health_posts: health_posts not in submitted_healthposts, health_posts)
    
            return late_healthpost
        


        @classmethod
        def list_by_location(cls, location, type=None):
            if location == None:
                health_posts = HealthPost.objects.all()
            else:
                health_posts = []
                for loc in location.descendants(include_self = True):
                        health_posts.append(cls.by_location(loc))
                health_posts = filter(lambda hp: hp != None , health_posts)
            if type != None:
                health_posts = filter(lambda hp: hp.type == type, health_posts)
            return health_posts

        @property
        def woreda(self):
            list = filter(lambda hp: hp.type.name.lower == "woreda", self.ancestors())
            
            if len(list) == 0:
                return None
            else:
                return list[0]

        def zone(self):
            list = filter(lambda hp: hp.type.name.lower == "zone", self.ancestors())
            
            if len(list) == 0:
                return None
            else:
                    return list[0]

        def region(self):
            list = filter(lambda hp: hp.type.name.lower == "region", self.ancestors())
            
            if len(list) == 0:
                return None
            else:return list[0]
                        

        def _get_number_of_child_locations(self):
            if self.type.name.lower() != "health post":
                locs = self.children.all()
                return len(locs)

        def _get_parent_location(self):
            if self.type.name.lower() !=  "region":
                return self.parent

        def _get_parent_location_name(self):
            if self.type.name.lower() != "region":
                return self.parent.name

        def _get_location_type(self):
                return self.type.name
               
        def _get_reporters(self):
            rep = []
            for reporter in OTPReporter.objects.all():
                if reporter.location.name == self.name:
                    rep.append(reporter)
            return rep
        
        def _get_reporters_name(self):
            reporters = self._get_reporters()
            reporters_name = ""
            for reporter in reporters:
                reporters_name = reporters_name + unicode(reporter) + ", "
            
            return reporters_name
 
        def _get_last_report(self):
                return "N/A"           

        number_of_child_location = property(_get_number_of_child_locations)
        parent_location = property(_get_parent_location)
        parent_location_name = property (_get_parent_location_name)
        location_type = property(_get_location_type)
        reporters = property(_get_reporters)
        last_report = property(_get_last_report)
        reporters_name = property(_get_reporters_name)
        



class Role(models.Model):
    """Basic representation of a role that someone can have.  For example,
       'supervisor' or 'data entry clerk'"""
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=20, blank=True, null=True,\
        help_text="Abbreviation")
        
    def __unicode__(self):
        return self.name


class OTPReporterConnection(Connection):
    class Meta:
	   verbose_name = "OTP Reporter Identity"

class OTPReporter(Contact):
    user_name = models.CharField(unique = True, max_length=30, help_text = "username must be unique")
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    grandfather_name = models.CharField(max_length=30, blank=True)
    
    location = models.ForeignKey(HealthPost, related_name="location", null=True, blank=True)
    role = models.ForeignKey(Role, related_name="roles", null=True, blank=True)
    email = models.EmailField(blank=True)
    is_active_reporter = models.BooleanField()
    	
    TITLE = _(u"OTP Reporter")

    class Meta:
        verbose_name = "OTP Reporter"
        ordering = ['first_name']
	
	# the string version of OTP reporter
	# now contains only their name i.e first_name last_name
    def __unicode__(self):
        return "%s %s" % (self.first_name, self.last_name)
    
	
	
    def _get_latest_report(self):
        try:
            return Entry.objects.filter(otp_reporter=self).order_by('-entry_time')[0]
        
        except IndexError:
            return "N/A"

    latest_report = property(_get_latest_report)
	
	
	
    # 'summarize' the HEWs by
    # returning his full name and phone number
    def _get_details(self):
        return "%s" % (self)
	
    details = property(_get_details)

    #the place where the health officer is assigned
    #returns the location name and its type (i.e woreda, zone, or region)
    def _get_place_assigned(self):
        return self.location
        
    place_assigned = property(_get_place_assigned)
    
    def _get_phone_number(self):
        try:
            return self.default_connection.identity
        except:
            return "N/A"
    
    phone = property(_get_phone_number)
    
    def _has_phone(self):
        if self.phone != None:
            return True
        else:
            return False
    
    has_phone = property(_has_phone)
    
    @property
    def title(self):
        return self.TITLE
    
    @classmethod
    def table_columns(cls):
        columns = []
        columns.append({'name': 'User name',})
        columns.append({'name': 'Full Name',})
        columns.append({'name': 'Health Post',})
        columns.append({'name': 'Woreda',})
        columns.append({'name': 'Phone',})
                        
        sub_columns = None
        
        return columns, sub_columns
    
    
    @classmethod
    def aggregate_report(cls, scope = None,location_type = None,
                         location_name = None, startmonth_id = None,
                         endmonth_id = None, group = None):
            results = []
    
            # healthposts in the scope of the webuser
            otp_reporters = scope.otp_reporters()
    
#            if location_type != "" and location_name != "":
#                    # Get all locations in the specified location
#                    loc_selected = HealthPost.objects.filter(
#                            name = location_name,
#                            type__name = location_type)[0]
#                    descendent_location = loc_selected.descendants(include_self = True)
#                    descendent_location_code = [des_loc.code for des_loc in descendent_location]
#                    otp_reporters = filter(lambda otp_reporters:
#                               otp_reporters.location.code in descendent_location_code, otp_reporters)
    
            if len(otp_reporters) == 0:
                    return results
    
            for otp_reporter in otp_reporters:
    #	                result = SortedDict()
    #	                result['first_name'] = otp_reporter.first_name
    #	                result['last_name'] = otp_reporter.last_name
    #	                #result['phone'] = otp_reporter.phone
    #	                result['location'] = otp_reporter.location.name 
    #	                results.append(result)
                    result = SortedDict()
                    result['reporter_id'] = otp_reporter.id
                    result['username'] = otp_reporter.user_name
                    result['first_name'] = "%s %s" % (otp_reporter.first_name, otp_reporter.last_name)
                    result['health_post'] = otp_reporter.location.name
                    result['woreda'] = otp_reporter.location.parent.name
                    result['phone'] = otp_reporter.phone
                    results.append(result)
                    
            return results
        
        
class LateHealthPost(models.Model):
    """ Model used to store late health post id and reporter's id
    with extended number of days. This model is updated every reporting period"""
    
    location = models.ForeignKey(HealthPost, help_text = "Name of late Healthposts")
    otp_reporter = models.ForeignKey(OTPReporter, help_text = "Name of active reporter in healthposts")
    accept_late_report = models.BooleanField(help_text = "Is the health post allowed to report late (for the current period)?")
    extended_days = models.PositiveIntegerField(default= 3, help_text="Number of days extended. (By default, it is set to 3 days)")

    class Meta:
        unique_together = ("location", "otp_reporter")

class Alert(models.Model):
    
    otp_reporter = models.ForeignKey(OTPReporter)
    time = models.DateTimeField(auto_now_add=True)
    notice = models.CharField(blank=True, max_length=160, help_text="Alert from Health extension worker")
    resolved = models.BooleanField(help_text="Has the alert been attended to?")
    
    def __unicode__(self):
    	return "%s by %s" %\
    	(self.time.strftime("%d/%m/%y"), self.otp_reporter)
    class Meta:
        ordering = ["-time"]    
        
class ReportPeriod(models.Model):
        month = models.CharField(max_length = 20, help_text="Report period month")
        year = models.PositiveIntegerField(help_text="Report period year")
        start_date = models.DateTimeField(help_text="Report period start date in GC")
        end_date = models.DateTimeField(help_text="Report period end date in GC")
        reporting_start_date = models.DateTimeField(help_text="Reporting period start date in GC")
        reporting_end_date = models.DateTimeField(help_text="Reporting period end date in GC (Deadline)")

        class Meta:
                unique_together = ("month", "year")
                get_latest_by = "month"
                

        def __unicode__(self):
                return "%s - %s" % (self.month,self.year)
            
            
        @classmethod    
        def list_from_boundries(cls, start, end):
            if start == end or end == None:
                return [start]
            if start.start_date > end.start_date:
                start, end = end, start
#            return start,end
            return cls.objects.filter(start_date__range=(start.start_date,
                                                        end.start_date))
class Configuration(models.Model):
	begining_admission = models.PositiveIntegerField(default=0,
													verbose_name="Begining OTP Patient")
	
	@classmethod
	def get_begining_admission(cls):
		return (cls.objects.values('begining_admission'))[0]['begining_admission']
	
	#begining = (property(_get_begining_admission))
		
	


	

class Entry(models.Model):
    TITLE = "OTP REPORT"
    class Meta:
    	get_latest_by="report_period"
        ordering = ["-entry_time"]			
    otp_reporter = models.ForeignKey(OTPReporter, help_text="Health Extension Worker")
    health_post = models.ForeignKey(HealthPost, help_text="The OTP site which this report was sent from")
    new_admission = models.PositiveIntegerField(default=0,
                            verbose_name=("Total Admited"))
    cured = models.PositiveIntegerField(default=0,
                            verbose_name=("Total Cured"))
    died = models.PositiveIntegerField(default=0,
                            verbose_name=("Total Death"))
    defaulted = models.PositiveIntegerField(default=0,
                            verbose_name=("Total Defaulter"))
    non_responded = models.PositiveIntegerField(default=0,
                            verbose_name=("Total Non Respondents"))
    medical_transfer = models.PositiveIntegerField(default=0,
                            verbose_name=("Total Medical Transfer"))
    tfp_transfer = models.PositiveIntegerField(default=0,
                            verbose_name=("Total TFP Transfer"))
    receipt =  models.CharField(blank=True, max_length=160, 
    						help_text="Receipt Number for Entry")
    late = models.BooleanField(help_text="Has the report made late?")
    confirmed_by_woreda = models.BooleanField(default=False)
    confirmed_by_zone = models.BooleanField(default=False)
    confirmed_by_region = models.BooleanField(default=False)
    #actual_admission=models.PositiveIntegerField(default=0,
    #                        verbose_name=("New Admission"))
    
    
    
    entry_time = models.DateTimeField(auto_now_add=True)
    report_period = models.ForeignKey(ReportPeriod, verbose_name="Period", help_text="The period in which the data is reported")
    
    #@classmethod
    #def _get_prev_entry(self,date):
    
    
    @classmethod	
    def get_entry_from_date(cls,date):
        start, end = ReportPeriod.weekboundaries_from_day(date)
        return cls.objects.filter(entry_time__range=(start,end))
    
    @classmethod	
    def get_prev_entry_from_date(cls,date):
        start, end = ReportPeriod.prev_weekboundaries_from_day(date)
        entry = cls.objects.filter(entry_time__range=(start,end)).order_by('-entry_time')
        return entry
    
    @classmethod	
    def get_entry_from_period(cls,period,healthpost):
        #start, end = ReportPeriod.prev_weekboundaries_from_day(date)
        #if healthpost==None:
        entry = cls.objects.filter(report_period__id=period,health_post__code=healthpost)[0]
        #else:
        #	entry = cls.objects.filter(report_period__id=period)
        #entry = cls.objects.filter(health_post__code=healthpost)
        return entry
    
    
    def get_actual_admission(self):
        #get pervious entry
        try:
        	prev_entry = Entry.objects.filter(report_period__id=int(self.report_period.pk)-1,health_post=self.health_post)[0]
        	actual_admission = self.new_admission - (prev_entry.new_admission - prev_entry.get_total_discharge())
        except(ObjectDoesNotExist,	IndexError):
        	actual_admission = self.new_admission - (Configuration.get_begining_admission())
        	
        return actual_admission
    
    
    def get_total_discharge(self):
        #get pervious entry
        
        #if prev_entry is not Nothing:
        total_discharge = self.cured + self.died + self.defaulted + self.non_responded + self.medical_transfer + self.tfp_transfer
        return total_discharge
    
    def get_total_remaining(self):
        return self.new_admission - self.get_total_discharge()
    
    def get_period_report(self):
        return self.report_period.pk
    
         
    def __unicode__(self):
        return "OTP data reported by %s from %s for period %s ." %\
        	(self.otp_reporter,self.health_post,self.report_period)
    
    
    def _get_receipt(self):
        self.receipt = ("%sM%s/%s") % \
                             (self.health_post.id,self.report_period.id,
                              self.id)
        return self.receipt
    receiptno = property(_get_receipt)
        
    @classmethod
    def table_columns(cls):
        columns = []
        columns.append(
        	{'name': cls._meta.get_field('new_admission').verbose_name})
        columns.append(
        	{'name': cls._meta.get_field('cured').verbose_name})
        columns.append(
        	{'name': cls._meta.get_field('died').verbose_name})
        columns.append(
        	{'name': cls._meta.get_field('defaulted').verbose_name})
        columns.append(
        	{'name': cls._meta.get_field('non_responded').verbose_name})
        columns.append(
        	{'name': cls._meta.get_field('medical_transfer').verbose_name})
        columns.append(
        	{'name': cls._meta.get_field('tfp_transfer').verbose_name})
        
        sub_columns=None
        return columns,sub_columns
	
    @classmethod
    def aggregate_report(cls,location,periods,loc):
        health_posts = HealthPost.list_by_location(location)
        hp=[]
        for healthpost in health_posts:
        	if healthpost.location_type=="health post":
        		hp.append(healthpost)
        		
        
        
        results = SortedDict()
        at = "none"
        
        for key in ['nadm','cured','died','defaulted','nresp','medt','tfpt']:
        	results[key] = None
        
        if loc.type.name == "zone":
        	otp_reports = Entry.objects.filter(report_period__in=periods, health_post__in=hp, confirmed_by_woreda=True)
        	
        	
        elif loc.type.name == "region":
        	otp_reports = Entry.objects.filter(report_period__in=periods, health_post__in=hp, confirmed_by_zone=True)
        	
        	
        elif loc.type.name == "federal":
        	otp_reports = Entry.objects.filter(report_period__in=periods, health_post__in=hp, confirmed_by_region=True)
        	
        else:
        	otp_reports = Entry.objects.filter(report_period__in=periods, health_post__in=hp)
        
        
        if otp_reports is not None:
        	if otp_reports.count() == len(hp) * len(periods):
        		results['complete'] = True
        	else:
        		results['complete'] = False
        
        q = otp_reports.aggregate(nadm=Sum('new_admission'),
        								cured=Sum('cured'),
        								died=Sum('died'),
        								defaulted=Sum('defaulted'),
        								nresp=Sum('non_responded'),
        								medt=Sum('medical_transfer'),
        								tfpt=Sum('tfp_transfer'))
        sum = Entry.objects.filter(report_period__in=periods, health_post__in=hp).extra(
        					select = {'total_exits': 'SUM(cured + died + defaulted + non_responded + medical_transfer + tfp_transfer)'},)[0]
        
        for key,value in q.items():
        	results[key] = value
    
    	return results
	
	
    @classmethod
    def aggregate_healthpost(cls,location,periods):
    	#hp = HealthPost.list_by_location(location)
        health_posts = HealthPost.list_by_location(location)
        hp=[]
        for healthpost in health_posts:
        	if healthpost.location_type=="health post":
        		hp.append(healthpost)
        
        results = SortedDict()
        otp_reports = Entry.objects.filter(report_period__in=periods, health_post__in=hp)
        if otp_reports.count() == len(hp) * len(periods):
        	results['complete'] = True
        else:
        	results['complete'] = False
        	
        for key in ['nadm','cured','died','defaulted','nresp','medt','tfpt','reporter']:
            results[key] = None	
        try:
            q = Entry.objects.filter(report_period__in=periods, health_post__in=hp)[0]
            
    #        for key,value in q.items():
            results['nadm'] = q.new_admission
            results['cured'] = q.cured
            results['died'] = q.died
            results['defaulted'] = q.defaulted
            results['nresp'] = q.non_responded
            results['medt'] = q.medical_transfer
            results['tfpt'] = q.tfp_transfer
            results['reporter'] =q.otp_reporter
        except:
            results = None
    
        return results
	
    @classmethod
    def aggregate_chart(cls,location,periods):
        #hp = HealthPost.list_by_location(location)
        health_posts = HealthPost.list_by_location(location)
        hp=[]
        for healthpost in health_posts:
        	if healthpost.location_type=="health post":
        		hp.append(healthpost)
        
        results = SortedDict()
        otp_reports = Entry.objects.filter(report_period=periods, health_post__in=hp)

        #mush check if the data is complete
        results['complete'] = True 
        
        for key in ['nadm','cured','died','defaulted','nresp','medt','tfpt', 'total_exit']:
            results[key] = None
        
        q = Entry.objects.filter(report_period=periods, health_post__in=hp).aggregate(nadm=Sum('new_admission'),
        								cured=Sum('cured'),
        								died=Sum('died'),
        								defaulted=Sum('defaulted'),
        								nresp=Sum('non_responded'),
        								medt=Sum('medical_transfer'),
        								tfpt=Sum('tfp_transfer'))
        #		sum = Entry.objects.filter(report_period=periods, health_post__in=hp).extra(
        #							select = {'total_exits': 'SUM(cured + died + defaulted + non_responded + medical_transfer + tfp_transfer)'},)
        
        for key,value in q.items():
            results[key] = value
        
        return results
	
	



class WebUser(User):
    ''' Extra fields for web users '''

    class Meta:
        pass

    def __unicode__(self):
        return unicode(self.user_ptr)

    # Use UserManager to get the create_user method, etc.
    objects = UserManager()

    location = models.ForeignKey(Location, blank=True, null=True)

    def health_posts(self):

        """
        Return the health posts within the location of the WebUser
        """
        if self.location == None:
            return HealthPost.objects.all()
        else:
            return HealthPost.list_by_location(self.location)

    def scope_string(self):
        if self.location == None:
            return 'All'
        else:
            return self.location.name

    def otp_reporters(self):

        """
        Return the otp reporters within
        the health posts of the related reporter
        """

        health_posts = self.health_posts()
        otp_reporters = []
        for otp_reporter in OTPReporter.objects.filter(role__code='hew'):
            if HealthPost.by_location(otp_reporter.location) in health_posts:
                otp_reporters.append(otp_reporter)
        return otp_reporters

    @classmethod
    def by_user(cls, user):
        try:
            return cls.objects.get(user_ptr=user)
        except cls.DoesNotExist:
            new_user = cls(user_ptr=user)
            new_user.save_base(raw=True)
            return new_user


