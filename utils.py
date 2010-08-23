from datetime import datetime, timedelta
from django.utils.text import capfirst
from django.utils import translation
from models import *

## {{{ http://code.activestate.com/recipes/576880/ (r1)
"""::::LICENSE::::
Copyright 2009 Jai Vikram Singh Verma (jaivikram[dot]verma[at]gmail[dot]com)

Licensed under the Apache License, Version 2.0 (the "License"); 
you may not use this file except in compliance with the License. 
You may obtain a copy of the License at 

http://www.apache.org/licenses/LICENSE-2.0 

Unless required by applicable law or agreed to in writing, 
software distributed under the License is distributed on an 
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, 
either express or implied. 
See the License for the specific language governing permissions 
and limitations under the License. 
"""

"""Module: parsedatetime

This module caters to the need of developers who
want to put time of post in terms on 
"X days, Y hrs ago", "A hours B mins ago", etc. 
in their applications rather then a basic timestamp
like "2009-08-15 03:03:00". Additionally it also 
provides since epoch for a given datetime.

It takes in a python datetime object as an input 
and provides a fancy datetime (as I call it) and
the seconds since epoch.

::::DISCLAIMER::::
1.  This module was written for my needs of this
    kind of datetime representation and it works just fine for me.
    If you feel there are imperfections, problems,
    etc. feel free to fix and publish, or bring them to my
    notice at the above mentioned email, I shall fix it.

2.  It does not take into consideration 31 day-month and  
    30 day-month, it jus uses 30 as a standard month-duration. 
    For the simple reason that if the developer
    wants to represent datetime as "X months, Y days ago" then 
    the relative importance of 30 or 31 is insignificant.

3.  It does not take leap years into consideration, again for the
    same reason when the representation is "X year, Y months ago"
    the relative importance of 365 or 366 is insignificant.

4. Again, in any given case it provides only two most significant 
   durations of time. e.g.: "1 year, 3 months, 2 days, 
   12 hours, 2 minutes ago" does not make sense, 'coz the gap is 
   large (in years), so the things beyond days (in this case) do
   not make much sense, hence the output shall be
   "1 year, 3 months ago".

Use, resuse, modify, contribute-back, have Fun!!
"""

import datetime
import time
import logging
logging.basicConfig(level = logging.DEBUG)
log = logging.getLogger('parsedatetime')

def makeEpochTime(date_time):
    """
    provides the seconds since epoch give a python datetime object.
    
    @param date_time: Python datetime object

    @return:
        seconds_since_epoch:: int 
    """
    date_time = date_time.isoformat().split('.')[0].replace('T',' ')
    #'2009-07-04 18:30:47'
    pattern = '%Y-%m-%d %H:%M:%S'
    seconds_since_epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return seconds_since_epoch 

def convertToHumanReadable(date_time):
    """
    converts a python datetime object to the 
    format "X days, Y hours ago"

    @param date_time: Python datetime object

    @return:
        fancy datetime:: string
    """
    current_datetime = datetime.datetime.now()
    delta = str(current_datetime - date_time)
    if delta.find(',') > 0:
        days, hours = delta.split(',')
        days = int(days.split()[0].strip())
        hours, minutes = hours.split(':')[0:2]
    else:
        hours, minutes = delta.split(':')[0:2]
        days = 0
    days, hours, minutes = int(days), int(hours), int(minutes)
    datelets =[]
    years, months, xdays = None, None, None
    plural = lambda x: 's' if x!=1 else ''
    if days >= 365:
        years = int(days/365)
        datelets.append('%d year%s' % (years, plural(years)))
        days = days%365
    if days >= 30 and days < 365:
        months = int(days/30)
        datelets.append('%d month%s' % (months, plural(months)))        
        days = days%30
    if not years and days > 0 and days < 30:
        xdays =days
        datelets.append('%d day%s' % (xdays, plural(xdays)))        
    if not (months or years) and hours != 0:
        datelets.append('%d hour%s' % (hours, plural(hours)))        
    if not (xdays or months or years):
        datelets.append('%d minute%s' % (minutes, plural(minutes)))        
    return ', '.join(datelets) + ' ago.'
    

def makeFancyDatetime(req_datetime):
    """
    a consolidate method to provide a nice output 
    taken from the other two methods as a dictionary,
    easily convertible to json.
    
    @param req_datetime: python datetime object
    
    @return:
        Python dictionay object with two key, value pairs
        representing 'fancy_datetime' and 'seconds_since_epoch'
    """
    return {'fancy_datetime': convertToHumanReadable(req_datetime), 
            'seconds_since_epoch': makeEpochTime(req_datetime)
            }

def test():
    """
    a small set of tests
    """
    bkwd_date = lambda x: datetime.datetime.now()-datetime.timedelta(seconds = x)
    siad = 60*60*24
    xs = [456, 365, 232, 23, 12.5, 0.5, 0.3]
    for x in xs:
        req_datetime = bkwd_date(siad*x)
        log.info("\nINPUT:  %s\nOutput:  %s\n*********" % \
                     (str(req_datetime), str(makeFancyDatetime(req_datetime))))


#if __name__ == '__main__':
#    test()
## end of http://code.activestate.com/recipes/576880/ }}}





# if the reporiting is done weekly, then the current reporting period
# is from monday upto sunday in the same week of the date

def current_reporting_period():
	"""Return a 2-tuple containing datetimes of the start and end
	of the current reporting period (the current calendar week) from monday to sunday"""
	
	# offsets are calculated from today use a datetime, because we
	# want the reporting period to end on the last second of sunday
	today = datetime.today().replace(
		hour=0, minute=0, second=0, microsecond=0)
	
	# reporting period spans the current week, from monday to sunday
	start = today - timedelta(days=today.weekday())
	end   = start + timedelta(days=7) - timedelta(seconds=1)
	
	# return a tuple
	return (start, end)

def get_or_generate_reporting_period():
        # Get or Generate reporting period
        start_date, end_date = current_reporting_period()
        period = ReportPeriod.objects.filter(
                start_date = start_date,
                end_date = end_date)

        if len(period) == 0:
                
                ReportPeriod.objects.create(
                        start_date = start_date,
                        end_date = end_date)
                return ReportPeriod.objects.latest()
        else:
                return period[0]
                


def nested_fields(model, max_depth=4):
	def iterate(model, nest=None):
		fields = []
		
		# iterate all of the fields in this model, and recurse
		# each foreign key to include fields from nested models
		for field in model._meta.fields:
			if nest is None: my_nest = [field]
			else: my_nest = nest + [field]
			
			# is this a foreign key? (also abort if depth is too deep)
			if (hasattr(field, "rel")) and (field.rel is not None) and (len(my_nest) <= max_depth):
				fields.extend(iterate(field.rel.to, my_nest))
			
			# add the field object as a tuple, including the
			# caption (containing prefixes) and the class itself
			else:
				filter = "__".join([f.name for f in my_nest])
				label = "/".join([capfirst(translation.ungettext(f.verbose_name, "", 1)) for f in my_nest])
				fields.append((filter, label, field))
		
		return fields

	# start processing at the top
	return iterate(model)
