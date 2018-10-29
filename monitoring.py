#!/usr/bin/python
import subprocess
import time
import syslog
import os
import sys
import socket

import settings

def send_mail(subject, in_msg):
        from email.mime.text import MIMEText
        from subprocess import Popen, PIPE

        msg = MIMEText(in_msg)
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = settings.EMAIL_TO
        msg["Subject"] = subject
        #print msg.as_string()
        p = Popen(["/usr/sbin/sendmail", "-t"], stdin=PIPE)
        p.communicate(msg.as_string())

def execute(process_args):
	child = subprocess.Popen(process_args.split(), stdout=subprocess.PIPE)
	streamdata = child.communicate()[0]
	rc = child.returncode
	return [rc, streamdata]


def main():
	state = {}
	

	first_loop = True
	while 1:

	  for item in settings.CHECKS:
		state=False
		notify=False

		if 'state' not in item:
			item['state'] = {'current':255, 'lastchange':0}

		# EXECUTE TEST
		process = "./check_"+item['type']
		if os.path.isfile(process):
			if type(item['arg']) is list:
				args = ' '.join(item['arg'])
			else:
				args = item['arg']
			res = execute(process+" "+args)
			state = res[0]
			info = res[1]
		else:
			print(process+" does not exists")
			sys.exit(-1)
		

		# STATE UPATE PROCESS
		if item['state']['current'] == state:
			if state != 0:
				elapsed = time.time()-item['state']['lastchange']
				print(elapsed)
				print(state, info)
				if elapsed > (settings.TIME_BETWEEN_NOTIFICATION*60):
					notify = True
					item['state']['lastchange'] = time.time()
		else:
			item['state']['current'] = state
			item['state']['lastchange'] = time.time()
			notify = True

		# MESSAGE GENERATION
		if notify:			
			if state == 0:
				state_header = "OK"
			elif state == 2:
				state_header = "WARNING"
			else:
				state_header = "CRITICAL"
			
			if state == 0:
				if 'critical-cmd' in item:
					subprocess.call(item['critical-cmd'], shell=True)
			
			elif state == 2:
				if 'warning-cmd' in item:
					subprocess.call(item['warning-cmd'], shell=True)

			else:
				if 'ok-cmd' in item:
					subprocess.call(item['ok-cmd'], shell=True)

			msg_header = "[ALERT] Monitoring: "+socket.gethostname()+" - "+ item['name']+" is "+state_header

			print(state, info)
			syslog.syslog(msg_header)
			print(msg_header)

			if (not first_loop) or state:
				send_mail(msg_header, info)

	  first_loop = False
	  time.sleep(60*settings.TIME_BETWEEN_CHECK)	

if __name__ == "__main__":
	main()

