import rapidsms
import re
from datetime import datetime
from strings import ENGLISH as STR

from django.core.management import setup_environ
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from rapidsms.apps.base import AppBase
#this shoud be locally available
from parsers.keyworder import * 
from models import *
#from apps.locations.models import *
from utils import *


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
            
    def __identify(self, message, task=None):
        caller = message.connection.identity
        otp_reporter = self.__get(OTPReporter, phone=caller)
		
	# if the caller is not identified, then send
	# them a message asking them to do so, and
	# stop further processing
	if not otp_reporter:
            msg = "Please register your mobile number"
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


    
    # ALERT <NOTICE> ----------------------------------------------------------
    kw.prefix = "alert"

    @kw("(whatever)")
    def alert(self, message, notice):
        caller = message.connection.identity
        otp_reporter = self.__identify(message,"alerting")
        Alert.objects.create(otp_reporter=otp_reporter, resolved=0, notice=notice)
        message.respond(STR["alert_ok"] % (otp_reporter.alias))
    
    @kw.blank()
    @kw(r"\s+")
    def alert_help(self, message, *msg):
        message.respond(STR["alert_help"])



    # CANCEL ------------------------------------------------------------------
    kw.prefix = ["cancel", "cancle"]

    @kw("(letters)")
    def cancel_code(self, message, code):
        caller = message.connection.identity
        otp_reporter = self.__identify(message, "cancelling")

        try:
            # attempt to find otp_reporter's 
            # entry with this code
            entry = Entry.objects.filter(
                    otp_reporter=otp_reporter,\
                    health_post__code=code,
                    entry_time__range=current_reporting_period())\
                    .order_by('-entry_time')[0]

            # delete it and notify
            entry.delete()
            message.respond(STR["cancel_code_ok"] % (code))

        except (ObjectDoesNotExist, IndexError):
#            try:
#                # try again for woreda code
#                entry = Entry.objects.filter(
#                        otp_reporter=otp_reporter,\
#                        supply_place__area__code=code)\
#                        .order_by('-time')[0]
#
#                # delete it and notify
#                entry.delete()
#                message.respond(STR["cancel_code_ok"] % (code))

#            except (ObjectDoesNotExist, IndexError):
            message.respond(STR["cancel_none"])

    @kw.blank()
    def cancel(self, message):
        caller = message.connection.identity
        rutf_reporter = self.__identify(message, "cancelling")
        
        try:
            # attempt to find the otp_reporter's
            # most recent entry TODAY
            latest = Entry.objects.filter(
                    time__gt=date.today(),
                    otp_reporter=otp_reporter)\
                    .order_by('-time')[0]
            latest_desc = latest.supply_place	
            # delete it and notify
            latest.delete()
            message.respond(STR["cancel_ok"] % (otp_reporter.alias, latest_desc))
        
        except (ObjectDoesNotExist, IndexError):
            message.respond(STR["cancel_none"] % (otp_reporter.alias))
    
    @kw.invalid()
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
    
    @kw.invalid()
    def help_help(self, message, *msg):
        message.respond(STR["help_help"])
        
    kw.prefix = ["otp","pp"]
    @kw(r'(\w+) (numbers) (numbers) (numbers) (numbers) (numbers) (numbers) (numbers)[,\.\s]*')
    def rept(self,message, place_code,na="",cu="", die="", df="", nr="", mt="", tt=""):
        #message.respond("%s %s %s %s %s %s %s %s" %(place_code,na,cu,die,df,nr,mt,tt))
        start_date,end_date = current_reporting_period()#ReportPeriod.weekboundaries_from_day(datetime.datetime.today())#current_reporting_period()
        caller = message.connection.identity
        otp_reporter = self.__identify(message, "reporting")
        #otp_reporter = self.__identity(message,"reporting")
        otpreporter = otp_reporter
        #message.respond("from %s to %s " %(start_date,end_date))
        loc= None
        pcu = place_code.upper()
        #message.respond("%s" %(pcu))
        loc = self.__get(HealthPost, code = pcu)
        if loc is None:
            message.respond(STR["unknown"]\
                %("Health Post, Woreda, or Zone code", pcu))
        
                
        try:
            #if there is a duplicate, it is assumed correction.
            e = Entry.objects.filter(otp_reporter=otp_reporter,entry_time__range=(start_date,end_date),health_post=loc).order_by('-entry_time')[0]
            if e is not None:
                e.delete()
                period = get_or_generate_reporting_period()
                Entry.objects.create(otp_reporter=otpreporter,
                                     health_post = loc,
                                     new_admission = na,
                                     cured=cu,
                                     died=die,
                                     defaulted=df,
                                     non_responded=nr,
                                     medical_transfer=mt,
                                     tfp_transfer=tt,
                                     report_period=period)
        except(ObjectDoesNotExist,IndexError):
            period = get_or_generate_reporting_period()
            Entry.objects.create(otp_reporter=otpreporter,
                                 health_post = loc,
                                 new_admission = na,
                                 cured=cu,
                                 died=die,
                                 defaulted=df,
                                 non_responded=nr,
                                 medical_transfer=mt,
                                 tfp_transfer=tt,
                                 report_period=period)
            
        info = ["admission=%s" % (na or "??"),
                "cured=%s" % (cu or "??"),
                "died=%s" % (die or "??"),
                "defaulted=%s" % (df or "??"),
                "non respondent=%s" % (nr or "??"),
                "medical transfer=%s" % (mt or "??"),
                "tfp transfer=%s" % (tt or "??")]
        
        if loc is not None:
            last_report = Entry.objects.filter(otp_reporter=otp_reporter,
                                               health_post = loc,
                                               new_admission=na,
                                               cured = cu,
                                               died = die,
                                               defaulted = df,
                                               non_responded=nr,
                                               medical_transfer =mt,
                                               tfp_transfer=tt).order_by('-report_period__id')[0]
            receipt = last_report.receipt
            message.respond("Received OTP Report for %s by %s: %s. If this is not correct, reply with CANCEL %s. Receipt No.=%s" %\
                (loc,otp_reporter,", ".join(info),loc,receipt))
            
    
            
    @kw.invalid()
    def help_report(self, message, *msg):
        message.respond("OTP REPORT ERROR : " + STR["help_report"])
                
        
        
#        message.respond("check Duplicate...")
#        message.respond("date range is.. from %s to %s" %(start_date,end_date))
#        message.respond("%s %s %s %s %s %s %s %s %s--%s" %(otpreporter,place_code,na,cu,die,df,nr,mt,tt,loc))
        
        
        
    

    kw.prefix = ["otpp","opt"]
    @kw(r'(\w+) (numbers) (numbers) (numbers) (numbers) (numbers) (numbers) (numbers)[,\.\s]*')
    def report(self, message, place_code, na="", cu="", die="", df="", nr="", mt="", tt=""):
        start_date,end_date = ReportPeriod.weekboundaries_from_day(datetime.datetime.today())#current_reporting_period()
        message.respond("__")
        otp_reporter = self.__identity(message,"reporting")
        otpreporter = otp_reporter
        message.respond("__")
        message.respond("from %s to %s " %(start_date,end_date))
        message.respond("__")
		#???validate each input if the reports are numbers
		#???new admission > total of the rest
		#some how it is allowing for unregistered phone...        
		# init variables to avoid
		# pythonic complaints	
        loc= None
        pcu = place_code
        message.respond("%s" %(pcu))
        loc = self.__get(HealthPost, code = pcu)
        messge.respond("%s - %s --> %s" % (otp_reporter, pcu, loc))
        if loc is None:
            message.respond(STR["unknown"])\
                %("Health Post, Woreda, or Zone code", pcu)
        message.respond("check Duplicate...")
        try:
            e = Entry.objects.filter(otp_reporter=otp_reporter,entry_time__range=(start_date,end_date)).order_by('-entry_time')[0]
            if e is not None:
                e.new_admission = na
                e.cured = cu
                e.died = die
                e.defaulted = df
                e.non_responded = nr
                e.medical_transfer = mt
                e.tfp_transfer = tt
                e.save()
        except(ObjectsDoesNotExist, IndexError):
            period = get_or_generate_reporting_period()
            Entry.objects.create(otp_reporter=otpreporter,
                                 health_post = loc,
                                 new_admission = na,
                                 cured=cu,
                                 died=die,
                                 defaulted=df,
                                 non_responded=nr,
                                 medical_transfer=mt,
                                 tfp_transfer=tt,
                                 report_period=period)
        info = ["admission=%s" % (na or "??"),
                "cured=%s" % (cu or "??"),
                "died=%s" % (die or "??"),
                "defaulted=%s" % (df or "??"),
                "non respondent=%s" % (nr or "??"),
                "medical transfer=%s" % (mt or "??"),
                "tfp transfer=%s" % (tt or "??")]
        
        if loc is not None:
            last_report = Entry.objects.filter(otp_reporter=otp_reporter,
                                               health_post = loc,
                                               new_admission=na,
                                               cured = cu,
                                               died = die,
                                               defaulted = df,
                                               non_responded=nr,
                                               medical_transfer =mt,
                                               tfp_transfer=tt).order_by('-report_period__id')[0]
            receipt = last_report.receipt
            message.respond("Received OTP Report for %s by %s: %s. If this is not correct, reply with CANCEL %s. Receipt No.=%s" %\
                (loc,otp_reporter,", ".join(info),loc,receipt))
        
    @kw.invalid()
    def help_report(self, message, *msg):
        message.respond("OTP REPORT ERROR : " + STR["help_report"])

       


    # NO IDEA WHAT THE CALLER WANTS -------------------------------------------
	
    def incoming_sms(self, message, msg):
        caller = message.connection.identity
        self.log("No match by regex", "warn")
        
        # we will only attempt to guess if
        # it looks like the caller is trying
        # to use these functions
        guess_funcs = (
                self.identify,
                self.report,
                self.alert)
        
        while(len(msg) > 0):
                found = False
                
                # iterate each guessable function, and each
                # of its regexen without their tailing DOLLAR.
                # since we couldn't find a real match, we're
                # looking for a matching prefix (in case the
                # sender has appended junk to their message,
                # or concatenated multiple messages without
                # proper delimitors)
                for func in guess_funcs:
                        for regex in getattr(func, "regexen"):
                                pattern = regex.pattern.rstrip("$")
                                new_regex = re.compile(pattern, re.IGNORECASE)
                                
                                # does the message START with
                                # the applied pattern?
                                match = new_regex.match(msg)
                                if match:
                                        
                                        # hack: since we're about to recurse via d_i_sms,
                                        # the chopped up message will be entered into the
                                        # database as if it were a real message, which will
                                        # confuse the log. this flag instructs before_incoming
                                        # to mark the following messages as virtual
                                        self.processing_virtual = True
                                        
                                        # log and dispatch the matching part, as if
                                        # it were a regular incoming message
                                        self.log("Prefix matches function: %s" % (func.func_name), "info")
                                        self.dispatch_incoming_sms(caller, match.group(0))
                                        
                                        # revert to normal behavior
                                        self.processing_virtual = False
                                        
                                        # drop the part of the message
                                        # that we just dealt with, and
                                        # continue with the next iteration
                                        msg = new_regex.sub("", msg, 1).strip()
                                        found = True
                                        break
                
                # nothing matched in this iteration,
                # so it won't ever. abort :(
                if not found:
                        self.log("No match for: %r" % (msg), "warn")
                        message.respond(STR["error"])




    # LOGGING -----------------------------------------------------------------
    
    # always called by smsapp, to log
    # without interfereing with dispatch
    def before_incoming(self, caller, msg):
            
            # we will log the rutf_reporter, if we can identify
            # them by their number. otherwise, log the number
            mon = self.__get(otp_reporter, phone=caller)
            if mon is None: ph = caller
            else: ph = None
            
            # don't log if the details are the
            # same as the transaction itself
            if mon == self.transaction.otp_reporter: mon = None
            if ph  == self.transaction.phone:   ph  = None
            
            # see above (hack) for explanation
            # of t his 'virtual' flag
            virt = False
            if hasattr(self, "processing_virtual"):
                    virt = self.processing_virtual
            
            # create a new log entry
            Message.objects.create(
                    transaction=self.transaction,
                    is_outgoing=False,
                    phone=caller,
                    otp_reporter=mon,
                    message=msg,
                    is_virtual=virt)
    
    
    # as above...
    def before_outgoing(self, recipient, msg):
            
            # we will log the rutf_reporter, if we can identify
            # them by their number. otherwise, log the number
            mon = self.__get(otp_reporter, phone=recipient)
            if mon is None: ph = recipient
            else: ph = None
            
            # don't log if the details are the
            # same as the transaction itself
            if mon == self.transaction.otp_reporter: mon = None
            if ph  == self.transaction.phone:   ph  = None
            
            # create a new log entry
            Message.objects.create(
                    transaction=self.transaction,
                    is_outgoing=True,
                    phone=recipient,
                    otp_reporter=mon,
                    message=msg)

    def getRouter(self):
        return self.router
