# -*- coding: utf-8 -*-
import urlparse
import os,sys
from string import *
import logging,requests
from urllib import *
from xml.dom import minidom
import xml.etree.ElementTree as ET
s=requests.Session()
#jen_url = "https://fusionapplvs01.qa.paypal.com:8443/jenkins/"
jen_url = "https://fusion.paypal.com/jenkins/"
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
doVerify = False
proxies={"http":"127.0.0.1:8888","https":"127.0.0.1:8888","ssl":"127.0.0.1:8888"}
cert=None#'test.pem'

#logger.info("current working space %s"%os.getcwd())
#if(doVerify and (not os.path.exists(cert))):
#    raise Exception("Cert file doesn't exist")
def deleteItem(jobname):
    logger.info("Update job %s"%jobname)
    url=urlparse.urljoin(jen_url,"job/%s/doDelete"%jobname)
    data={"Submit":"Yes",json:{}}
    res=s.post(url,data=data)	

def updateDescription(jobname):
    logger.info("Update job %s"%(jobname))
    api_url = urlparse.urljoin(jen_url,"job/%s/description"%jobname)
    report_url = urlparse.urljoin(jen_url,"job/%s/ws/target/surefire-reports/html/report.html"%jobname)
    desc="<br><br><a style=\"color:blue\" href=\"%s\"><font size =4>Bluefin HTML Report </font></a>"%report_url
    json = {"description":desc}
    res=s.post(api_url,data=json)
    if res.status_code !=204 and res.status_code !=200:
            logger.error("Failed to update job description: %s"%jobname)
           
def updateItem(jobname):
    raise Exception("updateItem is under construction")
	
def createItem(region,country,testsuite,chain):
    logger.info("Create test suite %s %s %s %s"%(region,country,testsuite,chain))
    url=urlparse.urljoin(jen_url,"/view/InternationalQA_View/view/%s/view/%s/view/%s/job/%s/configSubmit"%(quote("LQA Regression Testing"),region,country,testsuite))

def copyJob(jobname,jobnewname,viewurl):
    '''
    [Test passed]
    :param jobname:
    :param jobnewname:
    :param viewurl:
    '''
    json={"name": jobnewname, "mode": "copy", "from": jobname, "Submit": "OK"}
    copy_url = urlparse.urljoin(viewurl,"createItem")
    res=s.post(copy_url,data=json)
    if res.status_code != 200:
        raise Exception("Failed to copy job %s"%jobname)
	
def createJob(jobname,config):
    raise Exception("craeteJob is under construction")
	
def creatTestSuite(country,language,locale,testsuite):
    '''
    [deprecated]
    :param country:
    :param language:
    :param locale:
    :param testsuite:
    '''
    fsrc=open("%s\\france\\%s"%(workspace,testsuite),'r');
    testsuite=testsuite.replace("frFR","%s%s"%(language,locale))
    fdst=open("%s\\%s\\%s"%(workspace,lower(country),testsuite),'w')
    while(True):
        l=fsrc.readline()
        if(not l):
            break
        l=l.replace("FR",locale)
        fdst.write(l)
    fdst.close()
    fsrc.close()
    logger.info("Create local test suite file %s %s"%(country,testsuite))

def udpateAllJobsInView(viewurl,depth=1,fn,*args, **kwargs):
    if depth == 0:
        return
    view_api_url = urlparse.urljoin(lqa_url, "api/python?depth=%s"%depth)
    r = s.get(view_api_url)
    d = eval(r.text)
    for v in d['views']:
        udpateAllViewJobs(v['url'],depth=depth-1,fn,*args, **kwargs)
    fn(d['jobs'],*args, **kwargs)

def syncViewJobs(srcview,dstview,suffix="_Debug",docopy=False):
    '''
    [TEST PASSED]
    supports only two layers, for example the Region in LQA locale view
    :param srcview: 
    :param dstview:
    :param suffix:
    
    example:
        LQAview = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/LQA_Regression_Testing/view/%s/"%region
        AEview = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/AE_LQA_Regression_Testing/view/%s/"%regsion
        syncViewJobs(LQAview,AEview)
    example 2:
        LQAview = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/LQA_Regression_Flow_Testing/"
        AEview = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/AE_LQA_Regression_Testing/view/AE_Flow/"
        syncViewJobs(LQAview,AEview)
    
    '''
    lqa_url = urlparse.urljoin(jen_url,srcview)
    ae_url = urlparse.urljoin(jen_url,dstview)
    lqa_api_url = urlparse.urljoin(lqa_url, "api/python?depth=2")
    ae_api_url = urlparse.urljoin(ae_url, "api/python?depth=2")
#    lqa_api_url = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/LQA_Regression_Flow_Testing/api/python?depth=2"
#    ae_api_url = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/AE_LQA_Regression_Testing/view/AE_Flow/api/python?depth=2"
    flag = 0
    r = s.get(lqa_api_url)
    a = s.get(ae_api_url)
    lqa_conf = eval(r.text)
    ae_conf = eval(a.text)
    for lv in lqa_conf['views']:
        av = [ t for t in ae_conf['views'] if lv['name']==t['name']]
        if len(av) == 0:
           raise Exception("view %s doesn't exist"%lv['name']) 
        for lj in lv['jobs']:
            flag = flag +1
            aj = [ t for t in av[0]['jobs'] if (lj['name']+suffix).lower()==t['name'].lower() or lj['name'].lower()==(t['name']+suffix).lower()]
            if len(aj)==0:
                if docopy:
                    print lj['name'],av[0]['url']
                else:
                    newodename = lj['name']+suffix
                    copy_job(lj['name'],newodename,av[0]['url'])
                    updateDescription(newodename)
                    logger.info("Copied %s to %s under view %s"%(lj['name'],lj['name']+"_Debug",av[0]['url']))
    print "total job number: %s"%flag
	
def UpdateAllDescriptionInview(viewURL):
    '''
    [test passed]
    :param viewURL:
    '''
    logger.info("Update job description under view %s"%viewURL)
    r = s.get(viewURL+"/api/xml?depth=2")
    jobs = minidom.parseString(r.text.encode("utf8")).getElementsByTagName("job")
    logger.info("Found %s jobs"%len(jobs))
    while(len(jobs)>0):
        job = jobs.pop()
        joburl = job.getElementsByTagName("url")[0].firstChild.nodeValue
        updateDescription(joburl)
        #break
        
def login(username,password):
    url=urlparse.urljoin(jen_url,"j_acegi_security_check")
    json={"j_username": username, "j_password": password, "remember_me": "false", "from": ""}
    #res=s.post(url,data=json,verify=doVerify,proxies=None,cert=cert)
    res=s.post(url,data=json,verify=False)
    if(res.text.find('Invalid login information')>0):
        raise Exception("Failed to login")
    logger.info("user %s logged in successfully"%(username))
    #os.chdir(os.getcwd()+"\\..\\Localization\\localization-tests\\src\\test\\resources\\configfiles\\LqaRegressionTesting")
    #logger.info("Changed workdir to %s\\..\\Localization\\localization-tests\\src\\test\\resources\\configfiles\\LqaRegressionTesting"%(os.getcwd()))

if __name__=='__main__':
    login(sys.argv[1],sys.argv[2])
    LQAview = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/LQA_Regression_Testing/view/%s/"%region
    AEview = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/AE_LQA_Regression_Testing/view/%s/"%regsion
    LQAview_Flow = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/LQA_Regression_Flow_Testing/"
    AEview_Flow = "https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/AE_LQA_Regression_Testing/view/AE_Flow/"
    syncViewJobs(eval(sys.argv[3]),eval(sys.argv[4]),False)
    
    #UpdateAllDescriptionInview(urlparse.urljoin(jen_url,"/view/InternationalQA_View/view/LQA%20Regression%20Testing/")
    #UpdateAllDescriptionInview(urlparse.urljoin(jen_url,"/view/InternationalQA_View/view/AE%20Regression%20Testing/")
    #UpdateAllDescriptionInview(urlparse.urljoin(jen_url,"/view/DEQualityAutomation/")
    #UpdateAllDescriptionInview(urlparse.urljoin(jen_url,"/view/InternationalQA_View/view/%20New%20Regression/view/EMEA/view/Germany/")
    
