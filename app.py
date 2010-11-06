import rapidsms
import re
from datetime import datetime
from strings import ENGLISH as STR

from django.core.management import setup_environ
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from rapidsms.apps.base import AppBase

from parsers.keyworder import * 
from models import *
from utils import *

from tasks import testConsole


class App (AppBase):
    # lets use the Keyworder parser!
    kw = Keyworder()

    # non-standard regex chunks
    ALIAS = '([a-z\.]+)'

    
    def __get(self, model, **kwargs):
        try:
            # attempt to fetch the object
	    return model.objects.get(**kwargs) 
		
	# no objects or multiple objects found (in the latter case,
	# something is probably broken, so perhaps we should warn)
	except (ObjectDoesNotExist, MultipleObjectsReturned):
        	return None
     
     
    def __get_reporter(self, phone):
        try:
            # attempt to fetch the object
            reporters = []
            for reporter in OTPReporter.objects.all():
                if reporter.phone == phone:
                    reporters.append(reporter)

            if len(reporters) > 0:
                return reporters[0]
            else:
                return None
        
    # no objects or multiple objects found (in the latter case,
    # something is probably broken, so perhaps we should warn)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
                return None 
            
    def __identify(self, message, task=None):
        caller = message.connection.identity
        otp_reporter = self.__get_reporter(phone=caller)
		
	# if the caller is not identified, then send
	# them a message asking them to do so, and
	# stop further processing
	if not otp_reporter:
            msg = "Your phone is not registered. Please contact your supervisor"
            if task: msg += " before %s." % (task)
            #msg += ", by replying: I AM <USERNAME>"
            message.respond(msg)
            self.handled = True
		
	return otp_reporter


    def __monitor(self,message, alias):
	# some people like to include dots
	# in the username (like "a.mckaig"),
	# so we'll merrily ignore those
	clean = alias.replace(".", "")
		
	# attempt to fetch the rutf_reporter from db
	# (for now, only by their ALIAS...
	otp_reporter = self.__get(OTPReporter, alias=clean)
		
	# abort if nothing was found
	if not otp_reporter:
        	message.respond(STR["unknown_alias"] % alias)
		
	return otp_reporter
		    
    def __guess(self, string, within):
	try:
            from Levenshtein import distance
            import operator
            d = []
		
	# something went wrong (probably
	# missing the Levenshtein library)
	except:
            self.log("Couldn't import Levenshtein library", "warn")
            return None
		
	# searches are case insensitive
	string = string.upper()
		
	# calculate the levenshtein distance
	# between each object and the argument
	for obj in within:
		
            # some objects may have a variety of
            # ways of being recognized (code or name)
            if hasattr(obj, "guess"): tries = obj.guess()
            else: tries = [str(obj)]
			
            # calculate the intersection of
            # all objects and their "tries"
            for t in tries:
		dist = distance(str(t).upper(), string)
                d.append((t, obj, dist))
		
	    # sort it, and return the closest match
            d.sort(None, operator.itemgetter(2))
            if (len(d) > 0):# and (d[0][1] < 3):
		return d[0]
		
            # nothing was close enough
            else: return None


    def start (self):
        """Configure your app in the start phase."""
        self.startSchedule()
        #testConsole()
        
        
        pass
    
    def startSchedule(self):
        pass

        
        
    def parse (self, message):
        self.handled = False

    def handle (self, message):

        self.handled = False
        try:
            if hasattr(self,"kw"):
                self.debug("HANDLE")
                
                # attempt to match tokens in this message
                # using the keyworder parser
                results = self.kw.match(self, message.text)
                if results:
                    func, captures = results

                    # if a function was returned, then a this message
                    # matches the handler _func_. call it, and short-
                    # circuit further handler calls
                    func(self, message, *captures)
                    return self.handled
                else:
                    self.debug("NO MATCH FOR %s" % message.text)
            else:
                self.debug("App does not instantiate keyworder as 'kw'")
                
        except Exception, e:
            self.log_last_exception()
       

    def cleanup (self, message):
        """Perform any clean up after all handlers have run in the
           cleanup phase."""
        pass

    def outgoing (self, message):
        """Handle outgoing message notifications."""
        pass

    def stop (self):
        """Perform global app cleanup when the application is stopped."""
        pass


    
#    # ALERT <NOTICE> ----------------------------------------------------------
#    kw.prefix = "alert"
#
#    @kw("(whatever)")
#    def alert(self, message, notice):
#        caller = message.connection.identity
#        otp_reporter = self.__identify(message,"alerting")
#        Alert.objects.create(otp_reporter=otp_reporter, resolved=0, notice=notice)
#        message.respond(STR["alert_ok"] % ("%s %s" % (otp_reporter.first_name, otp_reporter.last_name)))
#    
#    @kw.blank()
#    @kw(r"\s+")
#    def alert_help(self, message, *msg):
#        message.respond(STR["alert_help"])
#
#
#
#    # CANCEL ------------------------------------------------------------------
#    kw.prefix = ["cancel", "cancle"]
#
#    @kw("(letters)")
#    def cancel_code(self, message, code):
#        caller = message.connection.identity
#        otp_reporter = self.__identify(message, "cancelling")
#        month, year, late , dates_gc = current_reporting_period()
#        period = get_or_generate_reporting_period()
#        #current_period = get_or_generate_reporting_period()
#        
#        #If late, notifiy 
#        if late == True:
#                message.respond("You can't cancel the report. It has been reported late. \
#                                Or it is late to cancel the report")
#        else:
#            try:
#                # attempt to find otp_reporter's 
#                # entry with this code
#                
#                entry = Entry.objects.filter(
#                        otp_reporter=otp_reporter,\
#                        health_post__code=code,
#                        report_period=period)\
#                        .order_by('-entry_time')[0]
#                        
#                if entry.late == True:
#                    message.respond("You can't cancel the report. It has been reported late. \
#                                Or it is late to cancel the report")
#                else:
#                    # delete it and notify
#                    entry.delete()
#                    message.respond(STR["cancel_code_ok"] % (code))
#                    
#                        
#            except (ObjectDoesNotExist, IndexError):
#                message.respond(STR["cancel_none"])

    # ALERT <NOTICE> ----------------------------------------------------------
    #kw.prefix = "[\"'\s]* alert [\.,\"'\s]*"

    @kw("[\"'\s]*alert[\"'\s]*(whatever)")
    def alert(self, message, notice):
        caller = message.connection.identity
        otp_reporter = self.__identify(message,"alerting")
        if otp_reporter is not None:
            Alert.objects.create(otp_reporter=otp_reporter, resolved=0, notice=notice)
            message.respond(STR["alert_ok"] % ("%s %s" % (otp_reporter.first_name, otp_reporter.last_name)))

    @kw.blank()
    @kw(r"\s+")
    def alert_help(self, message, *msg):
        message.respond(STR["alert_help"])



    # CANCEL ------------------------------------------------------------------
    kw.prefix = ["[\"'\s]*cancel", "[\"'\s]*cancle"]

    @kw("[\"'\s]*(letters)[\"'\s]*")
    def cancel_code(self, message, code):
        caller = message.connection.identity
        otp_reporter = self.__identify(message, "cancelling")

        try:
            # attempt to find otp_reporter's 
            # entry with this code in the current period

            month, year, late , dates_gc = current_reporting_period()
            period = get_or_generate_reporting_period()
            entry = Entry.objects.filter(
#                        otp_reporter=otp_reporter,\
                        health_post__code=code,
                        report_period=period)\
                        .order_by('-entry_time')[0]
            
            if (late == True or entry.late == True) and otp_reporter:
                message.respond("You can't cancel the report. It has been reported late.\
                                Or it is late to cancel the report")
            elif otp_reporter:
                # delete it and notify
                previous_reporter = entry.otp_reporter
                if otp_reporter == previous_reporter:
                    entry.delete()
                    healthpost_name = HealthPost.objects.get(code = code).name
                    message.respond(STR["cancel_code_ok"] % (healthpost_name))
                else:
                    message.respond("You can not cancel the report. \
                        The report is sent by %s %s" % (previous_reporter.first_name, previous_reporter.last_name) )

        except (ObjectDoesNotExist, IndexError):
            if late == False:
                message.respond(STR["cancel_none"] % period ) 
            else:
                message.respond(STR["cancel_late"])


    
    @kw.invalid()
    @kw.blank()
    def cancel_help(self, message, *msg):
        message.respond(STR["cancel_help"])

    # HELP <QUERY> ------------------------------------------------------------



    kw.prefix = ["help", "help me"]
    @kw.blank()
    def help_main(self, message):
        message.respond(STR["help_main"])
    
    @kw("report", "format", "fields")
    def help_report(self, message):
        message.respond(STR["help_report"])
    
    @kw("register", "identify") 
    def help_report(self, message):
        message.respond(STR["help_reg"])
    
    @kw("alert")
    def help_report(self, message):
        message.respond(STR["help_alert"])
    
    @kw("activate")
    def help_report(self, message):
        message.respond(STR["help_activate"])
    
    
    @kw.invalid()
    def help_help(self, message, *msg):
        message.respond(STR["help_help"])
        
#    kw.prefix = ["otp","opt"]
#    @kw(r'(\w+) (numbers) (numbers) (numbers) (numbers) (numbers) (numbers) (numbers)[,\.\s]*')
#    def rept(self,message, place_code,na="",cu="", die="", df="", nr="", mt="", tt=""):
#        month, year, late , dates_gc = current_reporting_period()
#        period = get_or_generate_reporting_period()
#        start_date,end_date = (dates_gc[2],dates_gc[3])
#        caller = message.connection.identity
#        otp_reporter = self.__identify(message, "reporting")
#        otpreporter = otp_reporter
#        loc= None
#        pcu = place_code.lower()
#        loc = self.__get(HealthPost, code = pcu)
#        if loc is None:
#            message.respond(STR["unknown"]\
#                %("Health Post, Woreda, or Zone code", pcu))
#                
#        
#        if otp_reporter and loc and otp_reporter.location == loc:          
#            try:
#                e = Entry.objects.filter(otp_reporter=otp_reporter,report_period=period,health_post=loc)[0]
#                if e is not None:
#                    if late==False:
#                        message.respond("REPORT NOT RECEIVED, A Report already exists. To correct, reply with < CANCEL %s > and send report again." %pcu)
#                    else:
#                        message.respond("CANNOT ACCEPT LATE REPORT, A report already exists.")
#            except(ObjectDoesNotExist,IndexError):
#                if late == False :
#                    period = get_or_generate_reporting_period()
#                    Entry.objects.create(otp_reporter=otpreporter,
#                                         health_post = loc,
#                                         new_admission = na,
#                                         cured=cu,
#                                         died=die,
#                                         defaulted=df,
#                                         non_responded=nr,
#                                         medical_transfer=mt,
#                                         tfp_transfer=tt,
#                                         report_period=period)
#                    
#                    info = ["admission=%s" % (na or "??"),
#                            "cured=%s" % (cu or "??"),
#                            "died=%s" % (die or "??"),
#                            "defaulted=%s" % (df or "??"),
#                            "non respondent=%s" % (nr or "??"),
#                            "medical transfer=%s" % (mt or "??"),
#                            "tfp transfer=%s" % (tt or "??")]
#                    if loc is not None:
#                        last_report = Entry.objects.filter(otp_reporter=otp_reporter,
#                                                           health_post = loc,
#                                                           new_admission=na,
#                                                           cured = cu,
#                                                           died = die,
#                                                           defaulted = df,
#                                                           non_responded=nr,
#                                                           medical_transfer =mt,
#                                                           tfp_transfer=tt).order_by('-report_period__id')[0]
#                        receipt = last_report.receiptno
#                        last_report.save()
#                        message.respond("Received OTP Report for %s by %s: %s. If this is not correct, reply with CANCEL %s. Receipt No.=%s" %\
#                        (loc,otp_reporter,", ".join(info),loc,receipt))
#                else:
#                    message.respond("Reporting deadline has passed, please contact the woreda health office.")
#        else:
#            message.respond("You can not send your report. please check the location code.")

    kw.prefix = ["[\"'\s]*otp[\"'\s]*","[\"'\s]*opt[\"'\s]*"]
    @kw(r'(\w+) (numbers) (numbers) (numbers) (numbers) (numbers) (numbers) (numbers)[,\.\s]*')
    def report(self,message, place_code,na="",cu="", die="", df="", nr="", mt="", tt=""):
        
        # ensure that the caller is known
        caller = message.connection.identity
        otp_reporter = self.__identify(message, "reporting")
        
        
        
        plc_code = place_code.upper()
        # the "place" can be Health post, woreda, or zone
        place = self.__get(HealthPost, code=plc_code)



        month, year, late , dates_gc = current_reporting_period()            
        
        if otp_reporter and place and otp_reporter.location == place and otp_reporter.is_active_reporter == True:
                        
            # init variables to avoid
            # pythonic complaints
            health_post = None
            woreda = None
            zone = None
            
                    
           
            
            # create the entry object, 
            # unless its a duplicate report in the period
                        
            period = get_or_generate_reporting_period()
            month_year = "%s-%s" % (month, year)
            try:
                entry = Entry.objects.filter(report_period=period,health_post=place)[0]

                if entry is not None:
                    previous_reporter_name = "%s %s" % (entry.otp_reporter.first_name,entry.otp_reporter.last_name)
                    current_reporter_name = "%s %s" % (otp_reporter.first_name,otp_reporter.last_name)

                    if late == False:
                        

                        if previous_reporter_name == current_reporter_name:
                            message.respond("You have already reported for %s Month. \
                                        If that was not correct, reply with CANCEL %s."
                                        % (month_year, place.code))
                        else:
                            message.respond("%s have already reported for %s Month.\
                                            The previous report should be canceled first."
                                        % (previous_reporter_name, month_year))
                            
                    else:
                        if previous_reporter_name == current_reporter_name:
                            message.respond("You have already reported for %s Month. \
                                        But now you are late to correct the previous report."
                                        % (month_year))
                        else:
                            message.respond("%s have already reported for %s Month. \
                                        But now you are late to correct the previous report."
                                        % (previous_reporter_name,month_year))
                    

            # If duplicate entry doesn't exist in the period
            except (ObjectDoesNotExist, IndexError):

                                      
                # add the entry
                # Get the reporting period

                if late == False:
                    Entry.objects.create(otp_reporter=otp_reporter,
                                         health_post = place, 
                                         new_admission = na, 
                                         cured=cu,died=die,
                                         defaulted=df,
                                         non_responded=nr, 
                                         medical_transfer=mt,
                                         tfp_transfer=tt, 
                                         report_period=period)
                
                    # collate all of the information submitted, to
                    # be sent back and checked by the reporter
                    info = ["admission=%s" % (na or "??"),
                            "cured=%s" % (cu or "??"),
                            "died=%s" % (die or "??"),
                            "defaulted=%s" % (df or "??"),
                            "non respondent=%s" % (nr or "??"),
                            "medical transfer=%s" % (mt or "??"),
                            "tfp transfer=%s" % (tt or "??")]
                    
                    # notify the reporter of their new entry
                    #if place is not None:
                    last_report = Entry.objects.filter(otp_reporter=otp_reporter,
                                                       health_post = place,
                                                       new_admission=na,
                                                       cured = cu,
                                                       died = die,
                                                       defaulted = df,
                                                       non_responded=nr,
                                                       medical_transfer =mt,
                                                       tfp_transfer=tt).order_by('-report_period__id')[0]
                        

                    # Generate receipt
                    new_receipt = last_report.receiptno
                    # then update the receipt value of the report
                    last_report.receipt = new_receipt
                    last_report.save()
                    
                    message.respond("Received OTP Report for %s by %s: %s. If this is not correct, reply with CANCEL %s. Receipt No.=%s" %\
                        (place,otp_reporter,", ".join(info),plc_code,new_receipt))
                else:
                    message.respond("You can not send your report. you are late.")
        else:
            if late == True and otp_reporter:
                message.respond("You can not send your report. you are late.")                
                
            elif otp_reporter:
                if otp_reporter.is_active_reporter == True:
                    reporter_location_code = otp_reporter.location.code
                    message.respond("You can not send your report. \
                        please check the supply code and the location code. \
                        Your location code is: %s" % reporter_location_code)
                else:
                    message.respond("Currently you are not active reporter. \
                        To activate yourself, please reply as: ACTIVATE")
                
   
            
    @kw.invalid()
    def help_report(self, message, *msg):
        caller = message.connection.identity
        otp_reporter = self.__identify(message, "reporting")
        if otp_reporter:
            message.respond("OTP REPORT ERROR : " + STR["help_report"])
        
    # set me active reporter ------------------------------------------------
    
    kw.prefix = ["[\"'\s]*activate[\"'\s]*", "[\"'\s]*activate [\"'\s]*me[\"'\s]*",
        "[\"'\s]*active[\"'\s]*", "[\"'\s]*set [\"'\s]*active[\"'\s]*"]
    @kw.blank()
    def activate_reporter(self, message):
        caller = message.connection.identity
        otp_reporter = self.__identify(message,"Activating")
        if otp_reporter is not None and otp_reporter.has_phone == True:
            # set other reporters in that location as inactive
            place_assigned = otp_reporter.place_assigned
            reporters = place_assigned.reporters
            for reporter in reporters:
                if reporter == otp_reporter:
                    otp_reporter.is_active_reporter = True
                    otp_reporter.save()
                    message.respond(STR["activate_ok"])
                else:
                    reporter.is_active_reporter = False
                    reporter.save()
                    
    @kw.invalid()
    def activate_help(self, message, *msg):
        message.respond(STR["activate_help"])


