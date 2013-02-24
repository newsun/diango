import logging
from jenkinsapi.jenkins import Jenkins
#try:
#	from jenkinsapi.jenkins import Jenkins
#except ImportError:
#	import sys
#	sys.path.append("jenkinsapi")
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
jen_url = "https://fusion.paypal.com/jenkins/"
username = "kejiang"
password = "Symbio@2013"
jen = Jenkins(jen_url,username,password)

def chain(jobsName,doChain=False):
    assert isinstance(jobsName,list)
    jobsName.sort()
    jobsName.reverse()
    chain = None
    for jobName in jobsName:
        job = jen[jobName]
        job.modify_chain(chain)
        logger.info("%s is chained to %s"%(chain,jobName))
        chain = doChain and jobName or chain

def goals(jobsName,newStr,oldStr=None,count=-1):
    goalsStr = "clean test -DstageName=${stageName} -DBLUEFIN_SELENIUM_HOST=10.57.88.98 -DBLUEFIN_HOSTNAME=${stageName}.${stageDomain}.paypal.com -DBLUEFIN_SSH_USER=${SSH_USER} -DJAWS_DEFAULT_EMAIL_PREFIX=${DEFAULT_EMAIL_PREFIX} -DJAWS_NIGHTOWL_MAIL_SERVER=nightowllvs01.qa.paypal.com -DsuiteXmlFile=src/test/resources/configfiles/LqaRegressionTesting/%s/%s.xml -Dpaypal.buildid=5333310"
    assert isinstance(jobsName,list)
    jobsName.sort()
    for jobName in jobsName:
        locale = jobName[3:7]
        job = jen[jobName]
        job.modify_goals(newStr,oldStr)
        logger.info("%s's goal is updated"%jobName)
        
def modify_view_jobs(url,fn,*args, **kwargs):
    view = jen.get_view_by_url(url)
    jobsName = view.get_jobs_list()
#    args_ = args.append(jobsName)
    fn(jobsName,*args, **kwargs)
    subviews = view.get_view_dict()
    for vn,vu in subviews.iteritems():
#        view = fv.get_view(vn)
        modify_view_jobs(vu,fn,*args, **kwargs)

def launch_all_flows():
    pass

if __name__=='__main__':
    username = "kejiang"
    password = "Symbio@2013"
    url = "https://fusion.paypal.com/jenkins/user/tkhoo/my-views/view/Flow%20View"
#    modify_view_jobs(url,chain,doChain=False)
    modify_view_jobs(url,goals,"-Dpaypal.buildid=5333310","-Dpaypal.buildid=\d+")
    
    
#	if jen.login():
#		logger.info(" %s login successfully"%username)
	#view = jen.get_view_by_url('https://fusion.paypal.com/jenkins/user/tkhoo/my-views/view/Flow%20View/view/Flow%2001/')
#	for fn in flows[:]:
#		viewURL = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/Horizontally%20chained%20view%20%28under%20construction%29/view/Per%20Flow/view/"+fn
#		view = jen.get_view_by_url(viewURL)
#		jobNames = view.get_job_dict().keys()
#		jobNames.sort()
#		print jobNames[0]
#		jen[jobNames[0]].invoke()		
#		break
#		jobNames.reverse()
#		chain = None
#		#job=jen[jobNames[0]]
#		for jn in jobNames:
#			if jn.find("jaJP")>0:
#				continue
#			#job = jen[jn]
#			#job.modify_chain(chain)
#			#job.modify_goals("","${DEFAULT_EMAIL_PREFIX_}")
#			#logger.info("%s is chained to %s"%(chain,jn))
#			chain=jn
#			#break
	