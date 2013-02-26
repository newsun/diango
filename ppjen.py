import sys
from urllib import *
import logging
from jenkinsapi.jenkins import Jenkins
from template import *
from optparse import OptionParser
import re
import ConfigParser
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
jen = None
jobs = []

def copyview(srcviewurl, dstViewurl,doAdd=False,suffix="_Debug"):
    srcview = jen.get_view_by_url(srcviewurl)
    dstview = jen.get_view_by_url(dstViewurl)
    for jobname in srcview.get_jobs_list():
        if doAdd:
            if not dstview.has_job(jobname):
                log = dstview.add_job(jobname)
                logger.info(log)
        else:
            newjobname = jobname + suffix
            if not dstview.has_job(newjobname):
                job = dstview.copy_job(jobname,newjobname)
                logger.info("job %s is copied to new view as %s"%(jobname,newjobname))
            
def modify_view_jobs(url,fn,*args, **kwargs):
    view = jen.get_view_by_url(url)
    jobsName = view.get_jobs_list()
    fn(jobsName,*args, **kwargs)
    subviews = view.get_view_dict()
    for vn,vu in subviews.iteritems():
#        view = fv.get_view(vn)
        modify_view_jobs(vu,fn,*args, **kwargs)

def joblist(jobsName):
    assert isinstance(jobsName,list)
    jobs.extend(jobsName)
    
def chain(jobsName,dochain=True):
    assert isinstance(jobsName,list)
    jobsName.sort()
    jobsName.reverse()
    chain = None
    for jobName in jobsName:
        job = jen[jobName]
        job.modify_chain(chain)
        logger.info("%s is chained to %s"%(chain,jobName))
        chain = dochain and jobName or chain

def goals(jobsName,newStr=None,oldStr=None,count=-1):
    assert isinstance(jobsName,list)
    goalsStr = "clean test -DstageName=${stageName} -DBLUEFIN_SELENIUM_HOST=10.57.88.98 -DBLUEFIN_HOSTNAME=${stageName}.${stageDomain}.paypal.com -DBLUEFIN_SSH_USER=${SSH_USER} -DJAWS_DEFAULT_EMAIL_PREFIX=${DEFAULT_EMAIL_PREFIX} -DJAWS_NIGHTOWL_MAIL_SERVER=nightowllvs01.qa.paypal.com -DsuiteXmlFile=%s -Dpaypal.buildid=5333310"
    jobsName.sort()
    for jobName in jobsName:
        job = jen[jobName]
        job.modify_goals(goalsStr%template[jobName.endswith("_Debug") and jobName[:-6] or jobName])
        logger.info("goals of %s has been updated"%jobName)

def defaultparameters(jobsName,params={}):
    assert isinstance(jobsName,list)
    jobsName.sort()
    for jobName in jobsName:
        job = jen[jobName]
        job.modify_predefined_parameters(params)
        logger.info("Default parameters of %s has been updated"%jobName)

def launch(jobsName,flow,stage,email,sshUser="ppbuild",domain="qa"):
    assert isinstance(jobsName,list)
    if len(jobsName)==0:
        return
    if re.match("\d+_\w+",flow):
        flow = flow[:3]
    if jobsName[0].lower().find(flow.lower())<0 :
        return
    jobsName.sort()
    jobName = jobsName[0]
    job = jen[jobName]
    params = {"stageName":stage,"SSH_USER":sshUser,"DEFAULT_EMAIL_PREFIX":email,"stageDomain":domain}
    job.invoke(params=params)
#    logger.info("Job %s has started"%jobName)
    
def launchall(jobsName, file):
    raise Exception("Under construction")
    assert isinstance(jobsName,list)
    try:
        from fileName import params
    except:
        raise Exception("file % doesn't exist")
        logger.info("Failed to lauch all flows")
    jobsName.sort()
    jobName = jobsName[0]
    flowName = jobName[:2]+jobName[7:]
    job = jen[jobName]
    job.invoke(params = params[flowName])

def compare_jobs(d1,d2):
    ae_flow_url = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/AE_LQA_Regression_Testing/view/AE_Flow/"
    ae_locale_url = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/AE_LQA_Regression_Testing/view/"
    lqa_flow_url = "https://fusion.paypal.com/jenkins/user/tkhoo/my-views/view/Flow%20View/"
    lqa_locale_url="https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/LQA_Regression_Testing/"
    
    s1 = eval(d1)
    s2 = eval(d2)
    
    modify_view_jobs(s1,joblist)
    global jobs
    joblist1 = jobs
    jobs=[]

    modify_view_jobs(s2,joblist)
    joblist2 = jobs
    jobs = []
#    ae = [a[:-6] for a in ae]
#    d1 = list(set(ae)-set(lqa))
#    d2 = list(set(lqa)-set(ae))
    return joblist1, joblist2

################ For Debug Only ##############
if __name__=='__main__':
#    if len(sys.argv) != 3:
#        sys.exit()
#    srcviewurl = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/LQA_Regression_Testing/view/%s/view/%s/"%(sys.argv[1],sys.argv[2])
#    dstviewurl = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/AE_LQA_Regression_Testing/view/%s/view/%s/"%(sys.argv[1],sys.argv[2])
#    jen = Jenkins(jen_url,"*","*")
#    copyview(srcviewurl,dstviewurl)
#    sys.exit()
#    modify_view_jobs(url,joblist)
#    modify_view_jobs(url,chain,doChain=False)
#    modify_view_jobs(url,goals,"-Dpaypal.buildid=5333310","-Dpaypal.buildid=\d+")"
#    sys.exit()
    usage = """
    This programe is to modify all the jobs under a given view and its sub views.
    python %prog [option][value]...
    Usage 1: python ppjen.py -u usename -p password -l viewurl -a chain [-c True|False]
    Usage 2: python ppjen.py -u usename -p password -l viewurl -a goals  [-n newStr [-o oldStr]]
    Usage 3: python ppjen.py -u usename -p password -l viewurl -a launch  [-s stage -e email]
    Usage 4: python ppjen.py -u usename -p password -l viewurl -a update_email -e email
    """
    parser = OptionParser(usage=usage,version="%prog 1.0")
    parser.add_option("-u","--username",dest="username",help="user name to login jenkins")
    parser.add_option("-p","--password",dest="password",help="user password to login jenkins")
    parser.add_option("-i","--view",dest="view",help="which view you want to operate. available: AE|LQA")
#    parser.add_option("-l","--url",dest="url",help="the view's url under which the jobs you want to update")
    parser.add_option("-a","--action",dest="action",help="the action you want to execute, valid values: [goals: update job's goals; chain: chain or unchain the jobs alphabetically; launch: launch a flow; launchAll: launch all flows")
    parser.add_option("-c","--dochain",dest="dochain",default = True, help="chain or unchain the jobs under a view")
    parser.add_option("-o","--oldStr",dest="oldStr",help="the old string (or a wildword expression) going to replace by new string, optioanl, default None")
    parser.add_option("-n","--newStr",dest="oldStr",help="the new string going to replace the oldstring, optional, default None")
    parser.add_option("-w","--flow",dest="flow",help="the flow name which is going to be launched")
    parser.add_option("-s","--stage",dest="stage",help="the stage for invoking a job")
    parser.add_option("-e","--email",dest="email",help="the email for invoking a job or default email")
    parser.add_option("-r","--sshuser",dest="ppuser",help="the ppuser for invoking a job")
    parser.add_option("-d","--domain",dest="domain",help="the stage domain for invoking a job")
    parser.add_option("-f","--file",dest="file",help="the configuration file")
    options,args = parser.parse_args()
    
    if options.file and not options.view:
        parser.error("if use conf file, you need choose a view type")
    elif options.file:
        config.readfp(open(options.file,'rb'))
        if options.view == "AE":
            config.getOption("AE View","url")
        elif options.view == "LQA":
            config.getOption("LQA View","url")
        else:
            raise Exception("Invalid view")
    if not options.username:
        parser.error("username can't be empty")
    if not options.url:
        parser.error("view url can't be empty")
    if not options.password:
        parser.error("password can't be empty")
    if not options.action:
        parser.error("action can't be empty")
    if options.action == "launch" and (not options.flow or not options.stage or not options.email):
        parser.error("lauch action needs flow name, stage and email")
    if options.action == "launchall" and (not options.file):
        parser.error("lauchall action needs configuration file")
    if options.action == "update_email" and not options.email:
        parser.error("update_email must accompany a new default email address prefix")

    jen = Jenkins(jen_url,options.username,options.password)
    if options.action == "launch":
        modify_view_jobs(options.url,eval(options.action),options.flow,options.stage,options.email)  
    elif options.action == "launchall":
        modify_view_jobs(options.url,eval(options.action),options.file)
    elif options.action == "chain":
        modify_view_jobs(options.url,eval(options.action),options.dochain)
    elif options.action == "goals":
        modify_view_jobs(options.url,eval(options.action),options.newStr,options.oldStr)
    elif options.action == "update_email":
        modify_view_jobs(options.url,eval(options.action),options.newStr,options.oldStr)
    else:
        raise Exception("invalid action")