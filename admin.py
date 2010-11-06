#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from django.contrib.auth import admin as auth_admin

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from locations.models import *
from models import *
import django.forms as forms








class OTPReporterConnectionInline(admin.TabularInline):
    model = OTPReporterConnection
    extra = 1


class OTPReporterAdmin(admin.ModelAdmin):
    inlines = [OTPReporterConnectionInline,]
    list_display = ('first_name', 'last_name', 'user_name', 'phone','is_active_reporter','location','latest_report')
    list_filter=['is_active_reporter','location']
    search_fields = ('^first_name', '^last_name', '^user_name')
    fields = ('user_name', 'first_name', 'last_name', 'grandfather_name', 'location', 'email', 'role', 'language', 'is_active_reporter')
    actions = ['set_reporter_active', 'set_reporter_inactive']
    

    #fields = ('first_name', 'last_name', 'grandfather_name','location')
    #filter_horizontal = ('groups',)
        
        #form = OTPReporterForm
        
    def queryset(self, request):
        qs = super(OTPReporterAdmin, self).queryset(request)
        webuser = WebUser.by_user(request.user)
        webuser_location = webuser.location
        if webuser_location is not None:
            child_locations = webuser_location.descendants(include_self = True)
            return qs.filter(location__in = child_locations)
        else:
            return qs
    
    
        
    def set_reporter_active(self, request, queryset):
        ''' Filter selected reporters who have phone number,
        and set them as active reporters. '''

        selected_reporters = len(queryset)
        reporters_with_phone = queryset.filter(connection__identity__isnull = False)
        rows_updated = 0
        for reporter in reporters_with_phone:
            place_assigned = reporter.place_assigned
            hp_reporters = place_assigned.reporters
            for hp_reporter in hp_reporters:
                if hp_reporter == reporter:
                    reporter.is_active_reporter = True
                    reporter.save()
                    rows_updated += 1
                else:
                    hp_reporter.is_active_reporter = False
                    hp_reporter.save()
                    
        rows_not_updated = selected_reporters - rows_updated
        
        # Display message to the user
        if rows_updated ==1:
            updated_no = "1 reporter was"
            success_message = "%s sucessfully set to active reporter" % updated_no
        elif rows_updated > 1:
            updated_no = "%s reporters were" % rows_updated
            success_message = "%s sucessfully set to active reporter" % updated_no

        if rows_not_updated == 1:
            not_updated_no = "1 reporter was"
            failure_message = "%s not set to active reporter.(No phone number registered)" % not_updated_no
        elif rows_not_updated > 1:
            not_updated_no = "%s reporters were" % rows_updated
            failure_message = "%s not set to active reporter.(May be no phone number registered)" % not_updated_no


        if rows_updated != 0 and rows_not_updated != 0:
            self.message_user(request, "%s. But %s" % (success_message,failure_message))
        else:
            if rows_updated != 0:
                self.message_user(request, "%s" % success_message)
            elif rows_not_updated != 0:
                self.message_user(request, "%s" % failure_message)

        

    def set_reporter_inactive(self, request, queryset):
        rows_updated = queryset.update(is_active_reporter = False)
        # Display message to the user
        if rows_updated ==1:
            message_no = "1 reporter was"
        elif rows_updated > 1:
            message_no = "%s reporters were" % rows_updated

        self.message_user(request, "%s sucessfully set to inactive reporter" % message_no)


class EntryAdmin(admin.ModelAdmin):
    list_display = ('health_post', 'otp_reporter', 'entry_time','confirmed_by_woreda', 'confirmed_by_zone' , 'confirmed_by_region')
    list_filter=['entry_time','confirmed_by_woreda', 'confirmed_by_zone' , 'confirmed_by_region']
    date_hierarchy = 'entry_time'
    ordering = ['entry_time']
    actions  = ['confirm_report','delete_selected']
    readonly_fields = ['confirmed_by_woreda','confirmed_by_region','confirmed_by_zone']
    
    def queryset(self, request):
        qs = super(EntryAdmin, self).queryset(request)
        webuser = WebUser.by_user(request.user)
        webuser_location = webuser.location
        child_locations = webuser_location.descendants(include_self = True)
        health_posts = HealthPost.objects.filter(name__in = child_locations)
        if webuser_location.type.name == "zone":
            return qs.filter(health_post__in = health_posts, confirmed_by_woreda = True)
        elif webuser_location.type.name == "region":
            return qs.filter(health_post__in = health_posts, confirmed_by_zone = True)
        elif webuser_location.type.name == "federal":
            return qs.filter(health_post__in = health_posts, confirmed_by_region = True)
        else:
            return qs.filter(health_post__in = health_posts)

    class ConfirmationForm(forms.Form):
            _selected_action = forms.CharField(widget = forms.MultipleHiddenInput)

    

    def confirm_report(self, request, queryset):
            form = None
            print "****************** admin confirmation ********* "
            for item in request.POST:
                print "%s %s" % (item, request.POST[item])
            if 'apply' in request.POST:
                form = self.ConfirmationForm(request.POST)

                if form.is_valid():
                    webuser = WebUser.by_user(request.user)
                    webuser_location = webuser.location
                    if webuser_location.type.name == "woreda":
                        # perform woreda level confirmation
                        rows_updated = queryset.update(confirmed_by_woreda = True)
                    elif webuser_location.type.name == "zone":
                        # perform zone level confirmation
                        rows_updated = queryset.update(confirmed_by_zone = True)
                    elif webuser_location.type.name == "region":
                        # perform region level confirmation
                        rows_updated = queryset.update(confirmed_by_region = True)

                    # Display message to the user
                    if rows_updated ==1:
                        message_no = "1 entry was"
                    elif rows_updated > 1:
                        message_no = "%s entries were" % rows_updated

                    self.message_user(request, "%s sucessfully confirmed" % message_no)

                    return HttpResponseRedirect(request.get_full_path())
                
            if not form:
                form = self.ConfirmationForm(
                    initial = {'_selected_action':request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})

            return render_to_response('admin/confirmation.html',
                                      {'entries':queryset,
                                       'confirmation_form':form,
                                       'path':request.get_full_path()},
                                      context_instance=RequestContext(request))
        
        
        
#    def confirm_report(self, request, queryset):
#        webuser = WebUser.by_user(request.user)
#        webuser_location =  webuser.location
#        if webuser_location.type.name == "woreda":
#            rows_updated = queryset.update(confirmed_by_woreda = True)
#        elif webuser_location.type.name == "zone":
#            rows_updated  = queryset.update(confirmed_by_zone =  True)
#        elif webuser_location.type.name ==  "region":
#            rows_updated = queryset.update(confirmed_by_region=True)
#        
#        if rows_updated == 1:
#            message_no = "1 entry"
#        elif rows_updated > 1:
#            message_no = "%s entries" %rows_updated
#            
#        self.message_user(request, "%s sucessfully confirmed" % message_no)
#        return HttpResponseRedirect("/otp/")
class LateHealthPostAdmin(admin.ModelAdmin):
    list_display = ('location', 'otp_reporter','accept_late_report', 'extended_days')
    list_filter = ['accept_late_report']
    search_fields = ('location', 'otp_reporter')
    actions = ['allow_late_report', 'deny_late_report']

    def allow_late_report(self, request, queryset):
        #rows_updated = queryset.update(accept_late_report = True)
        
        allowed_reporters = []
        reporters_messages = []
        today = datetime.now()
        new_deadline = None
        message = "Please send your report before %s"
        for late_healthpost in queryset:
            late_healthpost.accept_late_report = True
            late_healthpost.save()
        
            # new deadline
            new_deadline = today + timedelta(days=int(late_healthpost.extended_days))
            reporters_messages.append({"reporter": late_healthpost.otp_reporter, "message":message % new_deadline})
            allowed_reporters.append(late_healthpost.otp_reporter)
        
            EventSchedule.objects.create(callback='otpet.utils.deny_allowed_health_posts',
                                        months=set([new_deadline.month]),
                                        days_of_month=set([new_deadline.day]),
                                        hours = set([0]),
                                        minutes=set([0]),
                                        callback_kwargs = {"late_healthpost":late_healthpost})
            
        
        # send message to the reporter to
        # report with the extended days
        send_text_message(reporters_messages = reporters_messages)
        
        rows_updated = len(allowed_reporters)                  
        
        # Display message to the user
        if rows_updated ==1:
            message_no = "1 health post was"
        elif rows_updated > 1:
            message_no = "%s health posts were" % rows_updated
        
        self.message_user(request, "%s allowed to report late" % message_no)
                

    def deny_late_report(self, request, queryset):
        rows_updated = queryset.update(accept_late_report = False)

        # Display message to the user
        if rows_updated ==1:
            message_no = "1 health post was"
        elif rows_updated > 1:
            message_no = "%s health posts were" % rows_updated

        self.message_user(request, "%s denied to report late" % message_no)    
    
class HealthPostAdmin(admin.ModelAdmin):
    list_display = ('name', 'code','location_type','parent_location_name', 'latitude', 'longitude')
    list_filter = ['type']
    search_fields = ('name', 'code')
        
        #form = HealthPostForm
    def queryset(self, request):
        qs = super(HealthPostAdmin, self).queryset(request)
        webuser = WebUser.by_user(request.user)
        webuser_location = webuser.location
        if webuser_location is not None:
            child_locations = webuser_location.descendants(include_self = True)
            child_locations_code = [child_location.code for child_location in child_locations]
            return qs.filter(code__in = child_locations_code)
        else:
            return qs


        
        
        
class AlertAdmin(admin.ModelAdmin):
    list_display = ('otp_reporter', 'notice', 'time', 'resolved')
    list_filter = ['resolved', 'time']
    date_hierarchy = 'time'
    ordering = ['resolved']
    actions = ['resolve_alert', 'unresolve_alert']

    def queryset(self, request):
                qs = super(AlertAdmin, self).queryset(request)
                webuser = WebUser.by_user(request.user)
                webuser_location = webuser.location
                if webuser_location is not None:
                    child_locations = webuser_location.descendants(include_self = True)
                    #Select RUTF Reporters from the same location as the web-user
                    otp_reporters = OTPReporter.objects.filter(location__in = child_locations)
                    return qs.filter(otp_reporter__in = otp_reporters)
                else:
                    return qs
            

    def resolve_alert(self, request, queryset):
            rows_updated = queryset.update(resolved = True)

            # Display message to the user
            if rows_updated ==1:
                message_no = "1 alert was"
            elif rows_updated > 1:
                message_no = "%s alerts were" % rows_updated

            self.message_user(request, "%s sucessfully set to resloved state" % message_no)
                

    def unresolve_alert(self, request, queryset):
            rows_updated = queryset.update(resolved = False)

            # Display message to the user
            if rows_updated ==1:
                message_no = "1 alert was"
            elif rows_updated > 1:
                message_no = "%s alerts were" % rows_updated

            self.message_user(request, "%s sucessfully set to unresloved state" % message_no)


admin.site.register(Role)
admin.site.register(Alert, AlertAdmin)
admin.site.register(OTPReporter, OTPReporterAdmin)
#admin.site.register(LocationType)

admin.site.register(HealthPost, HealthPostAdmin)

admin.site.register(Entry, EntryAdmin)
admin.site.register(Configuration)

admin.site.register(WebUser)
admin.site.register(ReportPeriod)
admin.site.register(LateHealthPost, LateHealthPostAdmin)

admin.site.disable_action('delete_selected')
