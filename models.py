
from django.db import models
from django.contrib.auth import models as auth_models
from django.core.exceptions import ObjectDoesNotExist 

from datetime import date as pydate
from datetime import timedelta, datetime

from django.contrib.auth.models import User, UserManager
from django.utils.datastructures import SortedDict

##from utils import otp_code, woreda_code
from reporters.models import Reporter
from locations.models import Location, LocationType
##from utils import otp_code, woreda_code

from django.db.models import Sum


class OTPReporter(Reporter):
	grandfather_name = models.CharField(max_length=30, blank=True)
	phone = models.CharField(max_length=15, blank=True, help_text="e.g.,+251912555555")
	email = models.EmailField(blank=True)
		
	
	class Meta:
		verbose_name = "OTP Reporter"
		ordering = ['first_name']
	
	# the string version of RUTF reporter
	# now contains only their name i.e first_name last_name
	def __unicode__(self):
		return "%s %s" %\
			(self.first_name,
			self.last_name)
	
	def _get_latest_report(self):
		try:
			return Entry.objects.filter(otp_reporter=self).order_by('-time')[0]
		
		except IndexError:
			return "N/A"

	latest_report = property(_get_latest_report)
	
	
	
	# 'summarize' the HEWs by
	# returning his full name and phone number
	def _get_details(self):
		phone_number = self.phone or "unknown"
		return "%s (%s)" % (self, phone_number)
	
	details = property(_get_details)

	#the place where the health worker is assigned
	#returns the location name and its type (i.e woreda, zone, or region)
	def _get_place_assigned(self):
                place_name = "unknown"
                place_type = "unknown"
                return "%s %s" % (place_name, place_type)
        
        place_assigned = property(_get_place_assigned)

class HealthPost(Location, models.Model):
    
        
        def save(self):
		# if this Woreda or OTP_site does not already
		# have a code, assign a new one

		# For woreda
		if self.type.name.lower() == "woreda":
                    if(self.code == ""):
                            c = woreda_code()
                            self.code = c
                # For otp_site            
                if self.type.name.lower() == "otp_site":
                    if(self.code == ""):
                            c = otp_code()
                            self.code = c
		
		# invoke parent to save data
		models.Model.save(self)

	class Meta:
            ordering = ["name"]      

        #def __unicode__(self):
	#	return u'%s %s' % (self.name, self.type.name)

        def __unicode__(self):
		return u'%s' % (self.name)



	@classmethod
	def by_location(cls, location):
                try:
                        return cls.objects.get(location_ptr = location)
                except cls.DoesNotExist:
                        return None


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
                else:
                        return list[0]
                        

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

        number_of_child_location = property(_get_number_of_child_locations)

        parent_location = property(_get_parent_location)

        parent_location_name = property (_get_parent_location_name)

        location_type = property(_get_location_type)


class OTPSite(Location):
    catchment = models.PositiveIntegerField(null=True, blank=True)

    def __unicode__(self):
        return u'%s %s' % (self.name, self.type.name)

    @classmethod
    def by_location(cls, location):
        try:
            return cls.objects.get(location_ptr=location)
        except cls.DoesNotExist:
            return None

    @classmethod
    def list_by_location(cls, location, type=None):
        if location == None:
            otp_sites = OTPSite.objects.all()
        else:
            otp_sites  = []
            for loc in location.descendants(include_self=True):
                otp_sites.append(cls.by_location(loc))
            otp_sites = filter(lambda hc: hc != None, otp_sites)
        if type != None:
            otp_sites = filter(lambda hc: hc.type == type, otp_sites)
        return otp_sites

    @property
    def woreda(self):
        list = filter(lambda hc: \
                        hc.type.name.lower() == 'woreda', self.ancestors())
        if len(list) == 0:
            return None
        else:
            return list[0]

   
    #def up2date(self):
    #    if EpidemiologicalReport.last_completed_by_clinic(self) and \
    #       EpidemiologicalReport.last_completed_by_clinic(self).period == \
    #                                            ReportPeriod.objects.latest():
    #        return True
    #    else:
    #        return False










class Alert(models.Model):
	otp_reporter = models.ForeignKey(OTPReporter)
	time = models.DateTimeField(auto_now_add=True)
	notice = models.CharField(blank=True, max_length=160, help_text="Alert from Health extension worker")
	resolved = models.BooleanField(help_text="Has the alert been attended to?")
	
	def __unicode__(self):
		return "%s by %s" %\
		(self.time.strftime("%d/%m/%y"), self.reporter)


class ReportPeriod(models.Model):
        start_date = models.DateTimeField()
        end_date = models.DateTimeField()

        class Meta:
                unique_together = ("start_date", "end_date")
                get_latest_by = "end_date"
                ordering = ["-end_date"]

        def __unicode__(self):
                return "%s to %s" % (self.start_date,self.end_date)
	@classmethod
	def from_day(cls, day):
		start, end = cls.weekboundaries_from_day(day)
		try:
			return cls.objects.get(start_date=start, end_date=end)
		except cls.DoesNotExist:
			# create it and return
			period = cls(start_date=start, end_date=end)
			period.save()
			return period

	@classmethod
	def weekboundaries_from_day(cls, day):
		if day.weekday() < 7:
			# get previous week
			delta = day.weekday()
			startd = day - timedelta(delta)
			endd = startd + timedelta(6)
			start = datetime(startd.year, startd.month, startd.day)
			end = datetime(endd.year, endd.month, endd.day, 23, 59, 59)
			return (start, end)
		else:
			# sunday can't bind
			raise ErroneousDate
		
	@classmethod	
	def prev_weekboundaries_from_day(cls, day):
		if day.weekday() < 6:
			# get previous week
			delta = 7 + day.weekday()
			startd = day - timedelta(delta)
			endd = startd + timedelta(6)
			start = datetime(startd.year, startd.month, startd.day)
			end = datetime(endd.year, endd.month, endd.day, 23, 59, 59)
			return (start, end)
		else:
			# sunday can't bind
			raise ErroneousDate
		
	@classmethod	
	def list_from_boundries(cls, start, end):
		if start == end or end == None:
			return [start]
		if start.start_date > end.start_date:
			start, end = end, start
		return cls.objects.filter(start_date__range=(start.start_date,
													end.start_date))
		
		


	

class Entry(models.Model):

	TITLE = "OTP REPORT"
	class Meta():
		get_latest_by="report_period"			
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
		prev_entry = Entry.objects.filter(report_period__id=int(self.report_period.pk)-1,health_post=self.health_post)[0]
		#calculste actual admission
		actual_admission = self.new_admission - (prev_entry.new_admission - prev_entry.get_total_discharge())
		return actual_admission
	
	
	def get_total_discharge(self):
		#get pervious entry
		
		#if prev_entry is not Nothing:
		total_discharge = self.cured + self.died + self.defaulted + self.non_responded + self.medical_transfer + self.tfp_transfer
		return total_discharge
	
	def get_period_report(self):
		return self.report_period.pk
	
	     
	def __unicode__(self):
		return "OTP data reported by %s from %s for period %s ." %\
			(self.otp_reporter,self.health_post,self.report_period)

	def _get_receipt(self):
                return ("%sW%s/%s") % \
                             (self.health_post.id,self.report_period.id,
                              self.id)

                                 
        receipt = property(_get_receipt)
        
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
	def aggregate_report(cls,location,periods):
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
		
		for key in ['nadm','cured','died','defaulted','nresp','medt','tfpt']:
			results[key] = None
			
		q = Entry.objects.filter(report_period__in=periods, health_post__in=hp).aggregate(nadm=Sum('new_admission'),
										cured=Sum('cured'),
										died=Sum('died'),
										defaulted=Sum('defaulted'),
										nresp=Sum('non_responded'),
										medt=Sum('medical_transfer'),
										tfpt=Sum('tfp_transfer'))
		
		
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
        Return the rutf reporters within
        the health posts of the related reporter
        """

        health_posts = self.health_posts()
        otp_reporters = []
        for otp_reporter in OTPReporter.objects.filter(role__code='hew'):
            if HealthPost.by_location(rutf_reporter.location) in health_posts:
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


