import sys,os
import random
from urllib import *
import logging
from jenkinsapi.jenkins import Jenkins
from optparse import OptionParser
import re
import ConfigParser
import xml.etree.ElementTree as ET
###############################################
########### ppjen Configuration #############
###############################################
conf = ConfigParser.ConfigParser()
conf.read("ppjen.ini")
###############################################
########### Logging Configuration #############
###############################################
logging.basicConfig( level= logging.INFO,\
                 format= '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',\
                 datefmt= '%a, %d %b %Y %H:%M:%S',\
                 filename= 'ppjen_%s.log'%os.getpid(),\
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
    if isinstance(dochain,str):
        dochain = eval(dochain)
    jobsName.sort()
    jobsName.reverse()
    chain = None
    for jobName in jobsName:
#        if jobName.find("_jaJP_")>0:
#            conrugurumurthytinue
        job = jen[jobName]
        job.modify_chain(chain)
        logger.info("%s => %s"%(jobName,chain))
        chain = dochain and jobName or None
def permission(jobsName):
    assert isinstance(jobsName,list)
    goalsStr = "clean test -U -DstageName=${stageName} -DBLUEFIN_SELENIUM_HOST=10.57.88.98 -DBLUEFIN_HOSTNAME=${stageName}.${stageDomain}.paypal.com -DBLUEFIN_SSH_USER=${SSH_USER} -DJAWS_DEFAULT_EMAIL_PREFIX=${DEFAULT_EMAIL_PREFIX} -DJAWS_NIGHTOWL_MAIL_SERVER=nightowllvs01.qa.paypal.com -DsuiteXmlFile=%s -Dpaypal.buildid=%s"
    jobsName.sort()
    for jobName in jobsName:
        job = jen[jobName]
        config = job.get_config()
        element_tree = ET.fromstring(config)
        preprop = element_tree.find('./properties')
        permissionNode = element_tree.find('./properties/hudson.security.AuthorizationMatrixProperty')
        preprop.remove(permissionNode)
        permissionStr = getPermissionList()
        permissionNode = ET.fromstring(permissionStr)
        preprop.append(permissionNode)
        try:
            job.update_config(ET.tostring(element_tree))
        except:
            logger.error("Failed to update permission of job %s"%jobName)
        else:
            logger.info("Updated permission of job %s"%jobName)

def goals(jobsName,newStr=None,oldStr=None,count=-1):
    assert isinstance(jobsName,list)
    goalsStr = "clean test -U -DstageName=${stageName} -DBLUEFIN_SELENIUM_HOST=10.57.88.98 -DBLUEFIN_HOSTNAME=${stageName}.${stageDomain}.paypal.com -DBLUEFIN_SSH_USER=${SSH_USER} -DJAWS_DEFAULT_EMAIL_PREFIX=${DEFAULT_EMAIL_PREFIX} -DJAWS_NIGHTOWL_MAIL_SERVER=nightowllvs01.qa.paypal.com -DsuiteXmlFile=%s -Dpaypal.buildid=%s"
    jobsName.sort()
    for jobName in jobsName:
        job = jen[jobName]
        config = job.get_config()
        element_tree = ET.fromstring(config)
        goals = element_tree.find('./goals')
#        buildid = "-Dpaypal.buildid=%s"%random.randint(5000000,5999999)
        buildid = ""
        m = re.search(" -DsuiteXmlFile=(\S+\.xml) ",goals.text)
        if not m or len(m.groups())!=1:
            logger.error("Can't extract suite file in job %s"%jobName)
            continue
        testsuite = m.groups()[0]
        goals.text = goalsStr%("${%s_DEFAULT_EMAIL_PREFIX}"%locale,testsuite,buildid)
        
        logger.info("goals of %s has been updated"%jobName)
        
def getPermissionList():
    permType = ["hudson.model.Item.Workspace","hudson.model.Item.Build","hudson.model.Item.Cancel","hudson.model.Run.Update","hudson.model.Item.ExtendedRead","hudson.model.Item.Read","hudson.scm.SCM.Tag","hudson.model.Run.Delete","hudson.model.Item.Configure","hudson.model.Item.Delete"]
    ae = conf.options("AUTOMATION")
    tempT = lambda a,b:[(i,j) for i in a for j in b]
    perm = lambda p:"<permission>%s:%s</permission>"%(p[0],p[1])
    perms = "".join(map(perm,tempT(permType,ae)))
    anonymous = "".join(map(perm,tempT(permType[:3],["anonymous"])))
    pStr = "<hudson.security.AuthorizationMatrixProperty>%s%s</hudson.security.AuthorizationMatrixProperty>"%(perms,anonymous)
    return pStr

def getEmailNotification(locale):
    lqas = getLQAEmailList(locale)
    if len(lqas) == 0:
        raise Exception("No LQA defined for %s"%locale)
    elif len(lqas) == 1:
        lqarecipient = "${%s_DEFAULT_EMAIL_PREFIX}@paypal.com"%locale
    else:
        lqarecipient = "${%s_LQA_NOTIFICATION}"%locale

    aerecipient_list = "${FAILED_JOBS_NOTIFICATION}"
    mail = """<email><recipientList>%s</recipientList><subject>$PROJECT_DEFAULT_SUBJECT</subject><body>Hi,

We just finished running ${PROJECT_NAME}, we ran a total ${TEST_COUNTS, var="total"} testcases of which ${TEST_COUNTS, var="fail"} failed and ${TEST_COUNTS, var="skip"} were skipped.

Please review the results ${PROJECT_URL}ws/target/surefire-reports/html/report.html

Thanks,
Automation Team
DL-PayPal-LQA-Automation-Core-Symbio@corp.ebay.com</body><sendToDevelopers>false</sendToDevelopers><sendToRequester>false</sendToRequester><includeCulprits>false</includeCulprits><sendToRecipientList>true</sendToRecipientList></email>
"""
    aerecipient_list    
    email_notfications      = "<hudson.plugins.emailext.ExtendedEmailPublisher><recipientList></recipientList><configuredTriggers>%s</configuredTriggers><contentType>default</contentType><defaultSubject>$DEFAULT_SUBJECT</defaultSubject><defaultContent>$DEFAULT_CONTENT</defaultContent><attachmentsPattern/></hudson.plugins.emailext.ExtendedEmailPublisher>"
    UnstableTrigger         = "<hudson.plugins.emailext.plugins.trigger.UnstableTrigger>%s</hudson.plugins.emailext.plugins.trigger.UnstableTrigger>"%mail%"%s,%s"%(lqarecipient,aerecipient_list)
    FailureTrigger          = "<hudson.plugins.emailext.plugins.trigger.FailureTrigger>%s</hudson.plugins.emailext.plugins.trigger.FailureTrigger>"%mail%aerecipient_list
    StillFailingTrigger     = "<hudson.plugins.emailext.plugins.trigger.StillFailingTrigger>%s</hudson.plugins.emailext.plugins.trigger.StillFailingTrigger>"%mail%"%s,%s"%(lqarecipient,aerecipient_list)
    SuccessTrigger          = "<hudson.plugins.emailext.plugins.trigger.SuccessTrigger>%s</hudson.plugins.emailext.plugins.trigger.SuccessTrigger>"%mail%(lqarecipient)
    FixedTrigger            = "<hudson.plugins.emailext.plugins.trigger.FixedTrigger>%s</hudson.plugins.emailext.plugins.trigger.FixedTrigger>"%mail%(lqarecipient)
    StillUnstableTrigger    = "<hudson.plugins.emailext.plugins.trigger.StillUnstableTrigger>%s</hudson.plugins.emailext.plugins.trigger.StillUnstableTrigger>"%mail%"%s,%s"%(lqarecipient,aerecipient_list)
    email_notfications      = email_notfications%"%s%s%s"%(SuccessTrigger,UnstableTrigger,FailureTrigger)
    return email_notfications

def getLQAEmailList(locale):
    lqas = []
    lqas_ = conf.get("LQA",locale).split(",")
    for l in lqas_:
        if l.endswith("@ebay.com"):
            None
        elif l.endswith("@paypal.com"):
            None
        else:
            l = l+"@paypal.com"
        lqas.append(l)
    return lqas

def getDefaultEmailPrefix(email):
    pos = email.find("@")
    if pos <0:
        return email
    else:
        return email[:pos]
    
def getAEEmailList(flow):
    aes = []
    aes_ = conf.get("FLOW_OWENER",flow).split(",")
    for l in aes_:
        if l.endswith("@ebay.com"):
            None
        elif l.endswith("@paypal.com"):
            None
        else:
            l = l+"@paypal.com"
        aes.append(l)
    return aes

def getPredefinedParams(locale,flow):
    StringParames=[("stageName","","stage2dev463"),("stageDomain","","qa"),("SSH_USER","","ppbuild")]
    lqas = getLQAEmailList(locale)
    default_email_prefix = getDefaultEmailPrefix(lqas[0])
    if len(lqas) == 0:
        raise Exception("No LQA defined for %s"%locale)
    elif len(lqas) == 1:
        StringParames.append(("%s_DEFAULT_EMAIL_PREFIX"%locale,"Destination email prefix where the test case emails will be sent to and also will be notified when this job is Unstable or Success.",default_email_prefix))
    else:
        StringParames.append(("%s_DEFAULT_EMAIL_PREFIX"%locale,"Destination email prefix where the test case emails will be sent to",default_email_prefix))
        lqa_notification = ",".join(lqas)
        StringParames.append(("%s_LQA_NOTIFICATION"%locale,"Whom will be notified when this job is Unstable or Success.",lqa_notification))

    if locale == "deDE":
        ae = "rugurumurthy@paypal.com"
    else:
        ae = ",".join(getAEEmailList(flow))
    StringParames.append(("FAILED_JOBS_NOTIFICATION","whom will be notified when this job is Unstable,Failure. This can be a email list.",ae))
    fn = lambda p:"<hudson.model.StringParameterDefinition><name>%s</name><description>%s</description><defaultValue>%s</defaultValue></hudson.model.StringParameterDefinition>"%(p[0],p[1],p[2])
    StringParameterDefinitions = "".join(map(fn,StringParames))
    predefinedParams = "<hudson.model.ParametersDefinitionProperty><parameterDefinitions>%s</parameterDefinitions></hudson.model.ParametersDefinitionProperty>"%StringParameterDefinitions
    return predefinedParams
     
def config(jobsName):
    assert isinstance(jobsName,list)
    goalsStr = "clean test -U -DstageName=${stageName} -DBLUEFIN_SELENIUM_HOST=10.57.88.98 -DBLUEFIN_HOSTNAME=${stageName}.${stageDomain}.paypal.com -DBLUEFIN_SSH_USER=${SSH_USER} -DJAWS_DEFAULT_EMAIL_PREFIX=%s -DsuiteXmlFile=%s %s"
    
    for jobName in jobsName:
#        if jobName.find("01_")<0:
#            continue
#        if jobName.find(esAR")<0 and jobName.find("itIT")<0 and jobName.find("frCA")<0 and jobName.find("noNO")<0 and jobName.find("svSE")<0:
#            continue
#        print jobName
        m = re.search("(\d+_([^_]{4})_([^_]+)(_Part\d+)?)(_[D|d]ebug)?",jobName)
        if not m or len(m.groups())<3:
            logger.error("%s is not a valid job name"%jobName)
            continue
        jn =  m.groups()[0]
        locale = m.groups()[1]
        flow = m.groups()[2]
        if locale.lower() not in conf.options("LQA"):
            conf.set("LQA",locale,conf.get("LQA","default"))
            logger.warning("%s doesn't have LQA assigned"%locale)
        if flow.lower() not in conf.options("FLOW_OWENER"):
            logger.error("%s is a not supported flow"%jobName)
            continue
        job = jen[jobName]
        config = job.get_config()
        element_tree = ET.fromstring(config)
        #############################################permission change#############################################
        preprop = element_tree.find('./properties')
        permissionNode = element_tree.find('./properties/hudson.security.AuthorizationMatrixProperty')
        preprop.remove(permissionNode)
        permissionStr = getPermissionList()
        permissionNode = ET.fromstring(permissionStr)
        preprop.append(permissionNode)
        #############################################change goals#############################################
        goals = element_tree.find('./goals')
        m = re.search(" -DsuiteXmlFile=(\S+\.xml)\s*(-Dpaypal.buildid=\d+)?",goals.text)
        if not m or len(m.groups())<1:
            logger.error("Can't extract suite file in job %s"%jobName)
            continue
        testsuite = m.groups()[0]
        #        buildid = ""
        random_buildid = "-Dpaypal.buildid=%s"%random.randint(5000000,5999999)
        current_buildid = m.groups()[1]
        buildid =  current_buildid and current_buildid or random_buildid
        goals.text = goalsStr%("${%s_DEFAULT_EMAIL_PREFIX}"%locale,testsuite,buildid)
        #############################################change email notification################################
        publicsher = element_tree.find('./publishers')
        emailNoelement_tree = element_tree.find("./publishers/hudson.plugins.emailext.ExtendedEmailPublisher")
        if emailNoelement_tree is not None:
            publicsher.remove(emailNoelement_tree)
        email_notfication = getEmailNotification(locale)
        enn = ET.fromstring(email_notfication)
        publicsher.append(enn)
        ##############################################update the predefined parameter##########################
        predefinedParamsNode = element_tree.find('./properties/hudson.model.ParametersDefinitionProperty')
        if predefinedParamsNode is not None:
            preprop.remove(predefinedParamsNode)
        predefinedParams = getPredefinedParams(locale,flow)
        predefinedParamsNode = ET.fromstring(predefinedParams)
        preprop.append(predefinedParamsNode)
        ############################################## submit ##########################
        try:
            job.update_config(ET.tostring(element_tree))
        except:
            logger.error("Failed to configure %s"%jobName)
        else:
            logger.info("Updated %s"%jobName)
        
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
    s1 = eval(d1)
    s2 = eval(d2)
    
    modify_view_jobs(s1,joblist)
    global jobs
    joblist1 = jobs
    jobs=[]

    modify_view_jobs(s2,joblist)
    joblist2 = jobs
    jobs = []
    ae = [a[:-6] for a in ae]
    d1 = list(set(ae)-set(lqa))
    d2 = list(set(lqa)-set(ae))
    print d1
    print d2
    return joblist1, joblist2

################ For Debug Only ##############
if __name__=='__main__':
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
    parser.add_option("-v","--view",dest="view",help="which view you want to operate. available: AE|LQA")
    parser.add_option("-l","--url",dest="url",help="the view's url under which the jobs you want to update")
    parser.add_option("-a","--action",dest="action",help="the action you want to execute, valid values: [goals: update job's goals; chain: chain or unchain the jobs alphabetically; launch: launch a flow; launchAll: launch all flows")
    parser.add_option("-c","--dochain",dest="dochain",default = True, help="chain or unchain the jobs under a view")
#    parser.add_option("-o","--oldStr",dest="oldStr",default = None, help="the old string (or a wildword expression) going to replace by new string, optioanl, default None")
#    parser.add_option("-n","--newStr",dest="newStr",default = None, help="the new string going to replace the oldstring, optional, default None")
#    parser.add_option("-w","--flow",dest="flow",help="the flow name which is going to be launched")
#    parser.add_option("-s","--stage",dest="stage",help="the stage for invoking a job")
#    parser.add_option("-e","--email",dest="email",help="the email for invoking a job or default email")
#    parser.add_option("-r","--sshuser",dest="ppuser",help="the ppuser for invoking a job")
#    parser.add_option("-d","--domain",dest="domain",help="the stage domain for invoking a job")
#    parser.add_option("-f","--file",dest="file",help="the configuration file")
    options,args = parser.parse_args()
    
#    if options.file and not options.view:
#        parser.error("if use conf file, you need choose a view type")
#    elif options.file:
#        config.readfp(open(options.file,'rb'))
#        if options.view == "AE":
#            config.getOption("AE View","url")
#        elif options.view == "LQA":
#            config.getOption("LQA View","url")
#        else:
#            raise Exception("Invalid view")
    if not options.username:
        parser.error("username can't be empty")
    if not options.url and not options.view:
        parser.error("view can't be empty")
    if not options.password:
        parser.error("password can't be empty")
    if not options.action:
        parser.error("action can't be empty")
#    if options.action == "launch" and (not options.flow or not options.stage or not options.email):
#        parser.error("lauch action needs flow name, stage and email")
#    if options.action == "launchall" and (not options.file):
#        parser.error("lauchall action needs configuration file")
#    if options.action == "update_email" and not options.email:
#        parser.error("update_email must accompany a new default email address prefix")
    
    ae_flow = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/AE_LQA_Regression_Testing/view/AE_Flow/"
    ae_locale = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/AE_LQA_Regression_Testing/"
    lqa_flow = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/LQA_Regression_Flow_Testing/"
    lqa_locale ="https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/LQA_Regression_Testing/"
    jp = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/LQA_Regression_Testing/view/APAC/view/Japan/"
    if options.view:
        if options.view not in ["ae_flow","ae_locale","lqa_flow","lqa_locale","jp"]:
            parser.error("view can only be one of %s, %s, %s, or %s"%("ae_flow","ae_locale","lqa_flow","lqa_locale"))
        else:
            options.url = eval(options.view)
    actions = ['chain','config','permission']
    if options.action not in actions:
        parser.error("action can be one of %s"%str(actions))
    jen = Jenkins(jen_url,options.username,options.password)
    if options.action == "chain":
        modify_view_jobs(options.url,eval(options.action),options.dochain)
#    elif options.action == "launchall":
#        modify_view_jobs(options.url,eval(options.action),options.file)
#    elif options.action == "launch":
#        modify_view_jobs(options.url,eval(options.action),options.flow,options.stage,options.email)
#    elif options.action == "goals":
#        modify_view_jobs(options.url,eval(options.action),options.newStr,options.oldStr)
#    elif options.action == "update_email":
#        modify_view_jobs(options.url,eval(options.action),options.newStr,options.oldStr)
#    elif options.action == "compare_jobs":
#        modify_view_jobs(options.url,eval(options.action),options.newStr,options.oldStr)
    
    elif options.action == "config":
        modify_view_jobs(options.url,eval(options.action))
    elif options.action == "permission":
#         leftjobs = ["L10n_Step10_StageValidation_stage2dev473",
#"L10n_Step10_StageValidation_stage2dev470",
#"L10n_Step10_StageValidation_stage2dev474",
#"L10n_Step10_StageValidation_stage2dev475",
#"L10n_Step3_Deployment_Stage2p1444",
#"L10n_Step10_StageValidation_stage2p1446",
#"L10n_Step6_Restart_CustomerProfileSpartaWeb_stage2p1443",
#"L10n_Step8_Restart_addGlobalization_stage2p1443",
#"Set_CAPTCHA_CDB_Stage2p1443",
#"StageValidation_stage2dev461",
#"StageValidation_stage2dev463",
#"L10n_Step10_StageValidation_stage2dev462",
#"L10n_Step10_StageValidation_stage2dev465",
#"L10n_Step10_StageValidation_stage2dev464",
#"StageValidation_stage2dev466",
#"L10n_Step10_StageValidation_stage2dev469",
#"L10n_Step3_Deployment_Stage2p1494",
#"L10n_Step4_Restart_invoiceserv_stage2p1494",
#"L10n_Step5_Restart_ResolutionCenter_stage2p1494",
#"L10n_Step6_Restart_CustomerProfileSpartaWeb_stage2p1494",
#"L10n_Step7_Restart_Email_stage2p1494",
#"L10n_Step8_addGlobalization_stage2p1494",
#"Set_CAPTCHA_CDB_Stage2p1494"]
#         permission(leftjobs)
        modify_view_jobs(options.url,eval(options.action))
    else:
        raise Exception("invalid action")