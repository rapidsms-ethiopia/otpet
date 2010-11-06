#!/usr/bin/env python
# vim: noet

SUPPORT = "WOREDA OFFICE"
SORRY = "Sorry, I did not understand your message. "

ENGLISH = {
	"unknown_alias":  "I don't know anyone called %s",
	"unknown":        "The %s %s does not exist",
	"suggest":        "No such %s as %s. Did you mean %s (%s)?",
	"error":          SORRY + "For help, please reply: HELP",
	
	"ident":          "Hello, %s",
	"ident_again":    "Hello again, %s",
	"ident_help":     SORRY + "Please tell me who you are by replying: I AM YOUR-USERNAME",	
	
	"whoami":         "You are %s",
	"whoami_unknown": "I don't know who you are. Please tell me by replying: I AM YOUR-USERNAME",
	"whoami_help":    SORRY + "To find out who you are registered as, please reply: WHO AM I",
	
	"whois":          "%s is %s",
	"whois_help":     SORRY + "Please tell me who you are searching for, by replying: WHO IS USERNAME",

	"alert_ok":       "Thanks %s, Your alert was received",
	"alert_help":     SORRY + "Please tell me what you are alerting, by replying: ALERT YOUR-NOTICE",
	
	"activate_ok":     "You are set to active reporter. Now you can send report.",
    "activate_help":    SORRY + "To be an active reporter, reply as: ACTIVATE or ACTIVATE ME. You have to be registered first",
    
	"cancel_ok":      "Thanks %s, your %s report has been cancelled",	
	"cancel_code_ok": "Your last report for %s has been deleted",	
	"cancel_none":    "You have not submitted any reports for %s.",
	"cancel_late":    "You are late to cancel the report",
	"cancel_help":    "You may delete your last report by replying: CANCEL LOCATION-CODE",
	
	"supplies_help":  SORRY + "To list all supply codes, please reply: SUPPLIES",
	
	"help_main":   "HELP: reply with HELP ACTIVATE for activation, HELP REPORT for report formatting, or HELP ALERT for help with alerting",
	"help_help":   SORRY + "Please reply: HELP ACTIVATION, HELP REPORT or HELP ALERT",
	"help_report": "To make OTP report please send: OTP <OTP-Site> <NewAdmission> <Cured> <Died> <Defaulted> <Non-Responded> <Medical-Transfer> <TFP-Transfer>",
	"help_reg":  "If your mobile number is not registered, please reply: I AM YOUR-USERNAME",
	"help_alert":  "To send Alert, reply with: ALERT <your Message>",
	"help_activate": "To activate your self, reply with: ACTIVATE or ACTIVATE ME",

	"conv_welc": "You're welcome, %s!",
	"conv_greet": "Greetings, friend!",
	"conv_swear": "Would you text that to your mother, %s?"
}

