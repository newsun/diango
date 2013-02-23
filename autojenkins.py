import logging
try:
	from jenkinsapi.jenkins import Jenkins
except ImportError:
	import sys
	sys.path.append("jenkinsapi")
###############################################
########### Logging Configuration #############
###############################################
logging.basicConfig( level= logging.INFO,\
                 format= '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',\
                 datefmt= '%a, %d %b %Y %H:%M:%S',\
                 filename= 'myapp.log',\
                 filemode= 'w')

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger=logging.getLogger()
logger.addHandler(console)

###############################################

flows = ["01_SignUp","02_TransferFunds","03_SendMoney","04_RequestMoney","05_Transactions","06_Bank","07_CreditCard","08_Profile","09_Buttons","10_WebAccept","11_MainTabFeesFooter","13_PasswordRecovery","97_Limits","98_ResolutionCenter","99_ExpressCheckout"]	
	
if __name__=='__main__':
	jen_url = "https://fusion.paypal.com/jenkins/"
	username = "kejiang"
	password = "Symbio@2013"
	jen = Jenkins(jen_url,username,password)
	if jen.login():
		logger.info(" %s login successfully"%username)
	#view = jen.get_view_by_url('https://fusion.paypal.com/jenkins/user/tkhoo/my-views/view/Flow%20View/view/Flow%2001/')
	for fn in flows[:]:
		viewURL = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/Horizontally%20chained%20view%20%28under%20construction%29/view/Per%20Flow/view/"+fn
		view = jen.get_view_by_url(viewURL)
		jobNames = view.get_job_dict().keys()
		jobNames.sort()
		print jobNames[0]
		jen[jobNames[0]].invoke()		
		break
		jobNames.reverse()
		chain = None
		#job=jen[jobNames[0]]
		for jn in jobNames:
			if jn.find("jaJP")>0:
				continue
			#job = jen[jn]
			#job.modify_chain(chain)
			#job.modify_goals("","${DEFAULT_EMAIL_PREFIX_}")
			#logger.info("%s is chained to %s"%(chain,jn))
			chain=jn
			#break
	