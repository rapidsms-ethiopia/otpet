
from django.db import models
from django.contrib.auth import models as auth_models
from django.core.exceptions import ObjectDoesNotExist 

from datetime import date as pydate
from datetime import timedelta, datetime

from django.contrib.auth.models import User, UserManager

##from utils import otp_code, woreda_code
from reporters.models import Reporter
from locations.models import Location, LocationType
##from utils import otp_code, woreda_code




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


##class Report(models.Model):
##	supply = models.ForeignKey(Supply)
##	begin_date = models.DateField()
##	end_date = models.DateField()
##	supply_place = models.ForeignKey(SupplyPlace)
##
##	def __unicode__(self):
##		return "%s report" % self.supply.name
##	
##	def _get_latest_entry(self):
##		try:
##			e = Entry.objects.order_by('-time')[0]
##		except:
##			e = "No Entries"
##		return e
##	
##	def _get_number_of_entries(self):
##		return len(Entry.objects.filter(time__gte=self.begin_date).exclude(time__gte=self.end_date))
##
##	number_of_entries = property(_get_number_of_entries)
##	latest_entry = property(_get_latest_entry)
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
		if day.weekday() < 6:
			# get previous week
			delta = 7 + day.weekday()
			startd = day - timedelta(delta)
			endd = startd + timedelta(6)
			start = datetime(startd.year, startd.month, startd.day)
			end = datetime(endd.year, endd.month, endd.day, 23, 59)
			return (start, end)
		else:
			# sunday can't bind
			raise ErroneousDate


	

class Entry(models.Model):
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
	

	entry_time = models.DateTimeField(auto_now_add=True)
	report_period = models.ForeignKey(ReportPeriod, verbose_name="Period", help_text="The period in which the data is reported")
        
	def __unicode__(self):
		return "OTP data reported by %s from %s" %\
		(self.otp_reporter,self.health_post)

	def _get_receipt(self):
                return ("%sW%s/%s") % \
                             (self.health_post.id,self.report_period.id,
                              self.id)

                                 
        receipt = property(_get_receipt)


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


