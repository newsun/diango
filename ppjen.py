import sys
import random
from urllib import *
import logging
from jenkinsapi.jenkins import Jenkins
from template import *
from optparse import OptionParser
import re
import ConfigParser
import xml.etree.ElementTree as ET
#try:
#	from jenkinsapi.jenkins import Jenkins
#except ImportError:
#	import sys
#	sys.path.append("jenkinsapi")
###############################################
########### Logging Configuration #############
###############################################
logging.basicConfig( level= logging.DEBUG,\
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
LQA_corp = {"ruEE":["belzhang"],"deCH":["belzhang"],"deAT":["belzhang"],"daDK":["tbentzen"],"deDE":["aschilb"],"enGB":["dxiong"],"esAR":["elaguilar"],"esES":["pbrahm"],"esMX":["edugutierrez"],"frBE":["hsenouni"],"frCA":["vung","jsauvage"],"frCH":["vung"],"frFR":["jsauvage"],"heIL":["rshapiro"],"idID":["alaksanawati"],"itIT":["acantonetti"],"jaJP":["mkakeno"],"nlBE":["kocheng"],"nlNL":["kocheng"],"noNO":["hmoe"],"plPL":["rkonik"],"ptBR":["lheck"],"ptPT":["sealmeida"],"svSE":["richuang"],"thTH":["asrijanken"],"trTR":["yyakin"],"ruRU":["otulasynova"],"ruRU":["nafomina"],"zhC2":["klan"],"zhCN":["shuan"],"zhTW":["adguo"],"zhHK":["kamwong"],"enAU":["cdennington"]}
Flow_Owener = {"SignUp":["richuang","belzhang","rlux"],"TransferFunds":["belzhang","rlux"],"SendMoney":["bozhou","belzhang","rlux"],"RequestMoney":["rlux","belzhang","rlux"],"Transactions":["bozhou","belzhang","rlux"],"Bank":["belzhang","rlux"],"CreditCard":["rlux","belzhang","rlux"],"Profile":["bozhou","belzhang","rlux"],"Buttons":["belzhang","rlux"],"WebAccept":["jvely","belzhang","rlux"],"MainTabFeesFooter":["jvely","belzhang","rlux"],"PasswordRecovery":["richuang","belzhang","rlux"],"Limits":["richuang","belzhang","rlux"],"ResolutionCenter":["rlux","belzhang","rlux"],"ExpressCheckout":["belzhang","rlux"],"ExpressCheckoutOffeBay":["rugurumurthy"],"ExpressCheckoutOneBay":["rugurumurthy"]}

DE_SpecialFlow={
"BusinessSignUp":"rugurumurthy",
"BusinessSolutions":"rugurumurthy",
"ConfirmBank":"rugurumurthy",
"ConfirmBank":"rugurumurthy",
"ConfirmBank":"rugurumurthy",
"ConfirmBank":"rugurumurthy",
"EFTTransactions":"rugurumurthy",
"EFTTransactions":"rugurumurthy",
"MiscDETransactions":"rugurumurthy",
"mEFTSplashPage":"rugurumurthy",
"iEFTSplashPage":"rugurumurthy",
"MainTabFeesFooterDE":"rugurumurthy",
"SecurityHelpCenterDE":"rugurumurthy"
}

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
        if jobName.find("_jaJP_")>0:
            continue
        job = jen[jobName]
        job.modify_chain(chain)
        logger.info("%s is chained to %s"%(chain,jobName))
        chain = dochain and jobName or chain

def goals(jobsName,newStr=None,oldStr=None,count=-1):
    assert isinstance(jobsName,list)
    goalsStr = "clean test -U -DstageName=${stageName} -DBLUEFIN_SELENIUM_HOST=10.57.88.98 -DBLUEFIN_HOSTNAME=${stageName}.${stageDomain}.paypal.com -DBLUEFIN_SSH_USER=${SSH_USER} -DJAWS_DEFAULT_EMAIL_PREFIX=${DEFAULT_EMAIL_PREFIX} -DJAWS_NIGHTOWL_MAIL_SERVER=nightowllvs01.qa.paypal.com -DsuiteXmlFile=%s -Dpaypal.buildid=%s"
    jobsName.sort()
    for jobName in jobsName:
        jn = jobName.endswith("_Debug") and jobName[:-6] or jobName
        if jn not in template:
            logger.warning("%s is not in testsuite file defined"%jobName)
            continue
        job = jen[jobName]
        job.modify_goals(goalsStr%(template[jn],random.randint(5000000,5999999)))
        logger.info("goals of %s has been updated"%jobName)

def config(jobsName):
    assert isinstance(jobsName,list)
    permissionStr = "<hudson.security.AuthorizationMatrixProperty><permission>hudson.model.Item.Workspace:anonymous</permission><permission>hudson.model.Item.Workspace:kejiang</permission><permission>hudson.model.Item.Workspace:jvely</permission><permission>hudson.model.Item.Workspace:rlux</permission><permission>hudson.model.Item.Workspace:tkahkonen</permission><permission>hudson.model.Item.Workspace:sochoudhary</permission><permission>hudson.model.Item.Workspace:belzhang</permission><permission>hudson.model.Item.Workspace:richuang</permission><permission>hudson.model.Item.Workspace:linglu2</permission><permission>hudson.model.Item.Workspace:ltruong</permission><permission>hudson.model.Item.Workspace:tkhoo</permission><permission>hudson.scm.SCM.Tag:kejiang</permission><permission>hudson.scm.SCM.Tag:jvely</permission><permission>hudson.scm.SCM.Tag:rlux</permission><permission>hudson.scm.SCM.Tag:tkahkonen</permission><permission>hudson.scm.SCM.Tag:sochoudhary</permission><permission>hudson.scm.SCM.Tag:belzhang</permission><permission>hudson.scm.SCM.Tag:richuang</permission><permission>hudson.scm.SCM.Tag:linglu2</permission><permission>hudson.scm.SCM.Tag:ltruong</permission><permission>hudson.scm.SCM.Tag:tkhoo</permission><permission>hudson.model.Item.Delete:kejiang</permission><permission>hudson.model.Item.Delete:jvely</permission><permission>hudson.model.Item.Delete:rlux</permission><permission>hudson.model.Item.Delete:tkahkonen</permission><permission>hudson.model.Item.Delete:sochoudhary</permission><permission>hudson.model.Item.Delete:belzhang</permission><permission>hudson.model.Item.Delete:richuang</permission><permission>hudson.model.Item.Delete:linglu2</permission><permission>hudson.model.Item.Delete:ltruong</permission><permission>hudson.model.Item.Delete:tkhoo</permission><permission>hudson.model.Item.Configure:kejiang</permission><permission>hudson.model.Item.Configure:jvely</permission><permission>hudson.model.Item.Configure:rlux</permission><permission>hudson.model.Item.Configure:tkahkonen</permission><permission>hudson.model.Item.Configure:sochoudhary</permission><permission>hudson.model.Item.Configure:belzhang</permission><permission>hudson.model.Item.Configure:richuang</permission><permission>hudson.model.Item.Configure:linglu2</permission><permission>hudson.model.Item.Configure:ltruong</permission><permission>hudson.model.Item.Configure:tkhoo</permission><permission>hudson.model.Item.Build:anonymous</permission><permission>hudson.model.Item.Build:kejiang</permission><permission>hudson.model.Item.Build:jvely</permission><permission>hudson.model.Item.Build:rlux</permission><permission>hudson.model.Item.Build:tkahkonen</permission><permission>hudson.model.Item.Build:sochoudhary</permission><permission>hudson.model.Item.Build:belzhang</permission><permission>hudson.model.Item.Build:richuang</permission><permission>hudson.model.Item.Build:linglu2</permission><permission>hudson.model.Item.Build:ltruong</permission><permission>hudson.model.Item.Build:tkhoo</permission><permission>hudson.model.Run.Delete:kejiang</permission><permission>hudson.model.Run.Delete:jvely</permission><permission>hudson.model.Run.Delete:rlux</permission><permission>hudson.model.Run.Delete:tkahkonen</permission><permission>hudson.model.Run.Delete:sochoudhary</permission><permission>hudson.model.Run.Delete:belzhang</permission><permission>hudson.model.Run.Delete:richuang</permission><permission>hudson.model.Run.Delete:linglu2</permission><permission>hudson.model.Run.Delete:ltruong</permission><permission>hudson.model.Run.Delete:tkhoo</permission><permission>hudson.model.Item.Read:kejiang</permission><permission>hudson.model.Item.Read:jvely</permission><permission>hudson.model.Item.Read:rlux</permission><permission>hudson.model.Item.Read:tkahkonen</permission><permission>hudson.model.Item.Read:sochoudhary</permission><permission>hudson.model.Item.Read:belzhang</permission><permission>hudson.model.Item.Read:richuang</permission><permission>hudson.model.Item.Read:linglu2</permission><permission>hudson.model.Item.Read:ltruong</permission><permission>hudson.model.Item.Read:tkhoo</permission><permission>hudson.model.Item.ExtendedRead:kejiang</permission><permission>hudson.model.Item.ExtendedRead:jvely</permission><permission>hudson.model.Item.ExtendedRead:rlux</permission><permission>hudson.model.Item.ExtendedRead:tkahkonen</permission><permission>hudson.model.Item.ExtendedRead:sochoudhary</permission><permission>hudson.model.Item.ExtendedRead:belzhang</permission><permission>hudson.model.Item.ExtendedRead:richuang</permission><permission>hudson.model.Item.ExtendedRead:linglu2</permission><permission>hudson.model.Item.ExtendedRead:ltruong</permission><permission>hudson.model.Item.ExtendedRead:tkhoo</permission><permission>hudson.model.Run.Update:kejiang</permission><permission>hudson.model.Run.Update:jvely</permission><permission>hudson.model.Run.Update:rlux</permission><permission>hudson.model.Run.Update:tkahkonen</permission><permission>hudson.model.Run.Update:sochoudhary</permission><permission>hudson.model.Run.Update:belzhang</permission><permission>hudson.model.Run.Update:richuang</permission><permission>hudson.model.Run.Update:linglu2</permission><permission>hudson.model.Run.Update:ltruong</permission><permission>hudson.model.Run.Update:tkhoo</permission><permission>hudson.model.Item.Cancel:anonymous</permission><permission>hudson.model.Item.Cancel:kejiang</permission><permission>hudson.model.Item.Cancel:jvely</permission><permission>hudson.model.Item.Cancel:rlux</permission><permission>hudson.model.Item.Cancel:tkahkonen</permission><permission>hudson.model.Item.Cancel:sochoudhary</permission><permission>hudson.model.Item.Cancel:belzhang</permission><permission>hudson.model.Item.Cancel:richuang</permission><permission>hudson.model.Item.Cancel:linglu2</permission><permission>hudson.model.Item.Cancel:ltruong</permission><permission>hudson.model.Item.Cancel:tkhoo</permission></hudson.security.AuthorizationMatrixProperty>"
    goalsStr = "clean test -U -DstageName=${stageName} -DBLUEFIN_SELENIUM_HOST=10.57.88.98 -DBLUEFIN_HOSTNAME=${stageName}.${stageDomain}.paypal.com -DBLUEFIN_SSH_USER=${SSH_USER} -DJAWS_DEFAULT_EMAIL_PREFIX=%s -DJAWS_NIGHTOWL_MAIL_SERVER=nightowllvs01.qa.paypal.com -DsuiteXmlFile=%s %s"
    email_notfication= """
    <hudson.plugins.emailext.ExtendedEmailPublisher><recipientList></recipientList><configuredTriggers><hudson.plugins.emailext.plugins.trigger.UnstableTrigger><email><recipientList>%s,${FAILED_JOBS_NOTIFICATION}</recipientList><subject>$PROJECT_DEFAULT_SUBJECT</subject><body>Hi,

We just finished running ${PROJECT_NAME}, we ran a total ${TEST_COUNTS, var="total"} testcases of which ${TEST_COUNTS, var="fail"} failed and ${TEST_COUNTS, var="skip"} were skipped.

Please review the results ${PROJECT_URL}ws/target/surefire-reports/html/report.html

Thanks,
Automation Team
DL-PayPal-LQA-Automation-Core-Symbio@corp.ebay.com</body><sendToDevelopers>false</sendToDevelopers><sendToRequester>false</sendToRequester><includeCulprits>false</includeCulprits><sendToRecipientList>true</sendToRecipientList></email></hudson.plugins.emailext.plugins.trigger.UnstableTrigger><hudson.plugins.emailext.plugins.trigger.FailureTrigger><email><recipientList>%s,${FAILED_JOBS_NOTIFICATION}</recipientList><subject>$PROJECT_DEFAULT_SUBJECT</subject><body>Hi,

We just finished running ${PROJECT_NAME}, we ran a total ${TEST_COUNTS, var="total"} testcases of which ${TEST_COUNTS, var="fail"} failed and ${TEST_COUNTS, var="skip"} were skipped.

Please review the results ${PROJECT_URL}ws/target/surefire-reports/html/report.html

Thanks,
Automation Team
DL-PayPal-LQA-Automation-Core-Symbio@corp.ebay.com
</body><sendToDevelopers>false</sendToDevelopers><sendToRequester>false</sendToRequester><includeCulprits>false</includeCulprits><sendToRecipientList>true</sendToRecipientList></email></hudson.plugins.emailext.plugins.trigger.FailureTrigger><hudson.plugins.emailext.plugins.trigger.StillFailingTrigger><email><recipientList>%s,${FAILED_JOBS_NOTIFICATION}</recipientList><subject>$PROJECT_DEFAULT_SUBJECT</subject><body>Hi,

We just finished running ${PROJECT_NAME}, we ran a total ${TEST_COUNTS, var="total"} testcases of which ${TEST_COUNTS, var="fail"} failed and ${TEST_COUNTS, var="skip"} were skipped.

Please review the results ${PROJECT_URL}ws/target/surefire-reports/html/report.html

Thanks,
Automation Team
DL-PayPal-LQA-Automation-Core-Symbio@corp.ebay.com</body><sendToDevelopers>false</sendToDevelopers><sendToRequester>false</sendToRequester><includeCulprits>false</includeCulprits><sendToRecipientList>true</sendToRecipientList></email></hudson.plugins.emailext.plugins.trigger.StillFailingTrigger><hudson.plugins.emailext.plugins.trigger.SuccessTrigger><email><recipientList>%s</recipientList><subject>$PROJECT_DEFAULT_SUBJECT</subject><body>Hi,

We just finished running ${PROJECT_NAME}, we ran a total ${TEST_COUNTS, var="total"} testcases of which ${TEST_COUNTS, var="fail"} failed and ${TEST_COUNTS, var="skip"} were skipped.

Please review the results ${PROJECT_URL}ws/target/surefire-reports/html/report.html

Thanks,
Automation Team
DL-PayPal-LQA-Automation-Core-Symbio@corp.ebay.com</body><sendToDevelopers>false</sendToDevelopers><sendToRequester>false</sendToRequester><includeCulprits>false</includeCulprits><sendToRecipientList>true</sendToRecipientList></email></hudson.plugins.emailext.plugins.trigger.SuccessTrigger><hudson.plugins.emailext.plugins.trigger.FixedTrigger><email><recipientList>%s</recipientList><subject>$PROJECT_DEFAULT_SUBJECT</subject><body>Hi,

We just finished running ${PROJECT_NAME}, we ran a total ${TEST_COUNTS, var="total"} testcases of which ${TEST_COUNTS, var="fail"} failed and ${TEST_COUNTS, var="skip"} were skipped.

Please review the results ${PROJECT_URL}ws/target/surefire-reports/html/report.html

Thanks,
Automation Team
DL-PayPal-LQA-Automation-Core-Symbio@corp.ebay.com</body><sendToDevelopers>false</sendToDevelopers><sendToRequester>false</sendToRequester><includeCulprits>false</includeCulprits><sendToRecipientList>true</sendToRecipientList></email></hudson.plugins.emailext.plugins.trigger.FixedTrigger><hudson.plugins.emailext.plugins.trigger.StillUnstableTrigger><email><recipientList>%s,${FAILED_JOBS_NOTIFICATION}</recipientList><subject>$PROJECT_DEFAULT_SUBJECT</subject><body>Hi,

We just finished running ${PROJECT_NAME}, we ran a total ${TEST_COUNTS, var="total"} testcases of which ${TEST_COUNTS, var="fail"} failed and ${TEST_COUNTS, var="skip"} were skipped.

Please review the results ${PROJECT_URL}ws/target/surefire-reports/html/report.html

Thanks,
Automation Team
DL-PayPal-LQA-Automation-Core-Symbio@corp.ebay.com</body><sendToDevelopers>false</sendToDevelopers><sendToRequester>false</sendToRequester><includeCulprits>false</includeCulprits><sendToRecipientList>true</sendToRecipientList></email></hudson.plugins.emailext.plugins.trigger.StillUnstableTrigger></configuredTriggers><contentType>default</contentType><defaultSubject>$DEFAULT_SUBJECT</defaultSubject><defaultContent>$DEFAULT_CONTENT</defaultContent><attachmentsPattern/></hudson.plugins.emailext.ExtendedEmailPublisher>
    """
    #Default: stageName, SSH_USER, DEFAULT_EMAIL_PREFIX, stageDomain
#    predefinedParams = """
#        <hudson.model.ParametersDefinitionProperty><parameterDefinitions><hudson.model.StringParameterDefinition><name>stageName</name><description/><defaultValue>stage2dev463</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>SSH_USER</name><description/><defaultValue>ppbuild</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>DEFAULT_EMAIL_PREFIX</name><description/><defaultValue>%s</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>stageDomain</name><description/><defaultValue>qa</defaultValue></hudson.model.StringParameterDefinition></parameterDefinitions></hudson.model.ParametersDefinitionProperty>
#    """  
    # stageName, SSH_USER, DEFAULT_EMAIL_PREFIX, stageDomain, %s_NOTIFICATION_EMAIL, FAILED_JOBS_NOTIFICATION
#    predefinedParams = """
#        <hudson.model.ParametersDefinitionProperty><parameterDefinitions><hudson.model.StringParameterDefinition><name>stageName</name><description/><defaultValue>stage2dev463</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>SSH_USER</name><description/><defaultValue>ppbuild</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>DEFAULT_EMAIL_PREFIX</name><description>Destination email prefix where the test case emails will be sent to.</description><defaultValue>%s</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>stageDomain</name><description/><defaultValue>qa</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>%s_NOTIFICATION_EMAIL</name><description>whom will be notified when this job is Unstable,Failure,Still Failing, or Still Unstable. This can be a list of emails</description><defaultValue>%s</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>FAILED_JOBS_NOTIFICATION</name><description>whom will be notified when this job is Unstable,Failure,Still Failing,or Still Unstable. This can be a emails list.</description><defaultValue>%s</defaultValue></hudson.model.StringParameterDefinition></parameterDefinitions></hudson.model.ParametersDefinitionProperty>
#    """  
    # stageName, SSH_USER, %s_DEFAULT_EMAIL_PREFIX, stageDomain
#    predefinedParams = """
#        <hudson.model.ParametersDefinitionProperty><parameterDefinitions><hudson.model.StringParameterDefinition><name>stageName</name><description/><defaultValue>stage2dev463</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>SSH_USER</name><description/><defaultValue>ppbuild</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>%s_DEFAULT_EMAIL_PREFIX</name><description/><defaultValue>%s</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>stageDomain</name><description/><defaultValue>qa</defaultValue></hudson.model.StringParameterDefinition></parameterDefinitions></hudson.model.ParametersDefinitionProperty>
#    """
    # stageName, SSH_USER, stageDomain, %s_DEFAULT_EMAIL_PREFIX, FAILED_JOBS_NOTIFICATION
    predefinedParams = """
        <hudson.model.ParametersDefinitionProperty><parameterDefinitions><hudson.model.StringParameterDefinition><name>stageName</name><description/><defaultValue>stage2dev463</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>SSH_USER</name><description/><defaultValue>ppbuild</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>stageDomain</name><description/><defaultValue>qa</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>%s_DEFAULT_EMAIL_PREFIX</name><description>Destination email prefix where the test case emails will be sent to and also will be notified when this job is Unstable,Failure,Still Failing,Success,Fixed or Still Unstable.</description><defaultValue>%s</defaultValue></hudson.model.StringParameterDefinition><hudson.model.StringParameterDefinition><name>FAILED_JOBS_NOTIFICATION</name><description>whom will be notified when this job is Unstable,Failure,Still Failing,or Still Unstable. This can be a emails list.</description><defaultValue>%s</defaultValue></hudson.model.StringParameterDefinition></parameterDefinitions></hudson.model.ParametersDefinitionProperty>
    """  
    Flow_Owener.update(DE_SpecialFlow)
    for jobName in jobsName:
#        if jobName.find("01_daDK_SignUp_Debug")<0:
#            continue
#        if jobName.find("01_")<0:
#            continue
#        print jobName
        m = re.search("(\d+_([^_]{4})_([^_]+)(_Part\d+)?)(_[D|d]ebug)?",jobName)
        jn =  m.groups()[0]
        locale = m.groups()[1]
        flow = m.groups()[2]
        if not m:
            logger.error("%s is not a valid job name"%jobName)
            continue
        if locale not in LQA_corp:
            LQA_corp[locale]=["belzhang"]
            logger.warning("%s doesn't have LQA assigned"%jobName)
        if flow not in Flow_Owener:
            logger.error("%s is a not supported flow"%jobName)
            continue
        logger.debug("Flag 1")
        job = jen[jobName]
        logger.debug("Flag 2")
        config = job.get_config()
        logger.debug("Flag 3")
        element_tree = ET.fromstring(config)
        #############################################permission change#############################################
        preprop = element_tree.find('./properties')
        permissionNode = element_tree.find('./properties/hudson.security.AuthorizationMatrixProperty')
        preprop.remove(permissionNode)
        permissionNode = ET.fromstring(permissionStr)
        preprop.append(permissionNode)
        #############################################change goals#############################################
        if jn in template:
            goals = element_tree.find('./goals')
#            buildid = "-Dpaypal.buildid=%s"%random.randint(5000000,5999999)
            buildid = ""
#            goals.text = goalsStr%("${%s_DEFAULT_EMAIL_PREFIX}"%locale,template[jn],buildid)
            goals.text = goalsStr%("${%s_DEFAULT_EMAIL_PREFIX}"%locale,template[jn],buildid)
        else:
            goals = element_tree.find('./goals')
            print jobName, goals.text
            logger.warn("%s has no testsuite file defined"%jobName)
        #############################################change email notification################################
        publicsher = element_tree.find('./publishers')
        emailNoelement_tree = element_tree.find("./publishers/hudson.plugins.emailext.ExtendedEmailPublisher")
        if emailNoelement_tree is not None:
            publicsher.remove(emailNoelement_tree)
        LQA_NOTIFICATION_EMAIL = "${%s_DEFAULT_EMAIL_PREFIX}@paypal.com"%locale
        enn = ET.fromstring(email_notfication%(LQA_NOTIFICATION_EMAIL,LQA_NOTIFICATION_EMAIL,LQA_NOTIFICATION_EMAIL,LQA_NOTIFICATION_EMAIL,LQA_NOTIFICATION_EMAIL,LQA_NOTIFICATION_EMAIL))
        publicsher.append(enn)

        ##############################################update the predefined parameter##########################
        
        predefinedParamsNode = element_tree.find('./properties/hudson.model.ParametersDefinitionProperty')
        if predefinedParamsNode is not None:
            preprop.remove(predefinedParamsNode)

        DEFAULT_EMAIL_PREFIX = Flow_Owener[flow][0]
        xx_DEFAULT_EMAIL_PREFIX = LQA_corp[locale][0]
        LQA_NOTIFICATION_EMAIL = ",".join([e+"@paypal.com" for e in LQA_corp[locale]])
        FAILED_NOTIFICATION_EMAIL = ",".join([e+"@paypal.com" for e in Flow_Owener[flow]])
        
#        predefinedParamsNode = ET.fromstring(predefinedParams%(locale,xx_DEFAULT_EMAIL_PREFIX))
        predefinedParamsNode = ET.fromstring(predefinedParams%(locale,xx_DEFAULT_EMAIL_PREFIX,FAILED_NOTIFICATION_EMAIL))
        preprop.append(predefinedParamsNode)
        logger.debug("Flag 4")
        try:
            job.update_config(ET.tostring(element_tree))
        except:
            logger.error("%s fail to configure"%jobName)
            continue
        logger.debug("Flag 5")
        logger.info("%s has been updated"%jobName)
        
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
#    parser.add_option("-i","--view",dest="view",help="which view you want to operate. available: AE|LQA")
    parser.add_option("-l","--url",dest="url",help="the view's url under which the jobs you want to update")
    parser.add_option("-a","--action",dest="action",help="the action you want to execute, valid values: [goals: update job's goals; chain: chain or unchain the jobs alphabetically; launch: launch a flow; launchAll: launch all flows")
    parser.add_option("-c","--dochain",dest="dochain",default = True, help="chain or unchain the jobs under a view")
    parser.add_option("-o","--oldStr",dest="oldStr",default = None, help="the old string (or a wildword expression) going to replace by new string, optioanl, default None")
    parser.add_option("-n","--newStr",dest="newStr",default = None, help="the new string going to replace the oldstring, optional, default None")
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
    elif options.action == "compare_jobs":
        modify_view_jobs(options.url,eval(options.action),options.newStr,options.oldStr)
    elif options.action == "config":
        modify_view_jobs(options.url,eval(options.action))
    else:
        raise Exception("invalid action")