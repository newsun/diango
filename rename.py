# -*- coding: utf-8 -*-
import os
from string import *
import logging,requests
from urllib import *
from xml.dom import minidom
s=requests.Session()
workspace="..\\Localization\\localization-tests\\src\\test\\resources\\configfiles\\LqaRegressionTesting\\"
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
def deleteItem(region,country,testsuite,chain):
    logger.info("Update test suite %s %s %s %s"%(region,country,testsuite,chain))
    url="https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/%s/view/%s/view/%s/job/%s/doDelete"%(quote("LQA Regression Testing"),region,country,testsuite)
    logger.info(url)
    data={"Submit":"Yes",json:{}}
    res=s.post(url,data=data)	
def updateDescription(folder,region,country,testsuite):
    logger.info("Update test suite %s %s %s"%(region,country,testsuite))
    if folder.find("AE ")==0:
        testsuite=testsuite+"_Debug"
    url="https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/%s/view/%s/view/%s/job/%s/description"%(quote(folder),region,country,testsuite)
    desc="<br><br><a style=\"color:blue\" href=\"https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/%s/view/%s/view/%s/job/%s/ws/target/surefire-reports/html/report.html\"><font size =4>Bluefin HTML Report </font></a>"%(quote(folder),region,country,testsuite)
    json = {"description":desc}
    res=s.post(url,data=json)
    if res.status_code !=204 and res.status_code !=200:
            logger.error("Failed to update test suite description: %s %s %s"%(region,country,testsuite))
def updateDescription(joburl):
    logger.info("Update test suite %s"%(joburl))
    url=joburl+"description"
    desc="<br><br><a style=\"color:blue\" href=\"%sws/target/surefire-reports/html/report.html\"><font size =4>Bluefin HTML Report </font></a>"%(joburl)
    json = {"description":desc}
    res=s.post(url,data=json)
    if res.status_code !=204 and res.status_code !=200:
            logger.error("Failed to update test suite description: %s"%joburl)
            
def updateItem(region,country,testsuite,chain):
    logger.info("Update test suite %s %s %s %s"%(region,country,testsuite,chain))
    url="https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/%s/view/%s/view/%s/job/%s/configSubmit"%(quote("LQA Regression Testing"),region,country,testsuite)
    url2="https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/%s/view/%s/view/%s/job/%s/config.xml"%(quote("LQA Regression Testing"),region,country,testsuite)
    logger.info(url)
    goals="clean test -DstageName=${stageName} -DBLUEFIN_SELENIUM_HOST=10.57.88.98 -DBLUEFIN_HOSTNAME=${stageName}.${stageDomain}.paypal.com -DBLUEFIN_SSH_USER=${SSH_USER} -DJAWS_DEFAULT_EMAIL_PREFIX=${DEFAULT_EMAIL_PREFIX} -DJAWS_NIGHTOWL_MAIL_SERVER=nightowllvs01.qa.paypal.com -DsuiteXmlFile=src/test/resources/configfiles/LqaRegressionTesting/%s/%s.xml -Dpaypal.buildid=4982456"%(country,testsuite)
    files={'file':('config.xml',open('configuration.xml','rb'))}
    #res=s.post(url,data=jobconf_str,proxies=None,verify=False)
    res=s.post(url2,files=files)
    print res.text
    f=open("updateItem.html",'w')
    f.write(res.text)
    f.close()
	
def createItem(region,country,testsuite,chain):
    logger.info("Create test suite %s %s %s %s"%(region,country,testsuite,chain))
    url="https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/%s/view/%s/view/%s/job/%s/configSubmit"%(quote("LQA Regression Testing"),region,country,testsuite)

def copyItem(srcTestSuite,dstView,region,country,testsuite):
    url="https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/%s/view/%s/view/%s/createItem"%(quote(dstView),region,country)
    try:
        res=s.get(url)
        logger.info("%s %s %s %s %s already exists"%(dstView,region,country,testsuite,chain))
        #return
    except:
            print ""        
    logger.info("Copy test suite %s %s %s"%(region,country,testsuite))
    logger.info(url)
    json={"name": testsuite, "mode": "copy", "from": srcTestSuite, "Submit": "OK"}
    res=s.post(url,data=json)
	
def createJob(dstView,region,country,testsuite,chain):
    url="https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/%s/view/%s/view/%s/job/%s"%(quote(dstView),region,country,testsuite)
    try:
        res=s.get(url)
        logger.info("%s %s %s %s already exists"%(region,country,testsuite,chain))
        #return
    except:
            print ""
    #copyItem(testsuite,"LQA Regression Testing",region,country,testsuite)
    #updateItem(region,country,testsuite,chain)
    #deleteItem(region,country,testsuite,chain)
	
def creatTestSuite(country,language,locale,testsuite):
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

def creat(region,country,language,locale):
    logger.info("current workspace: "+os.getcwd())
    if(not os.path.exists(workspace+lower(country))):
        os.makedirs(workspace+lower(country))
    chain=""
    testsuites=os.listdir(workspace+"france")
    testsuites.reverse()
    for f in testsuites:
	logger.info("testsuite file: "+f)
        creatTestSuite(country,language,locale,f)
        f=f[:-4].replace("frFR","%s%s"%(language,locale))
        createJob(region,country,f,chain)
        chain=f
def main(region,country,language,locale):
    logger.info("current workspace: "+os.getcwd())
    if(not os.path.exists(workspace+lower(country))):
        os.makedirs(workspace+lower(country))
    chain=""
    testsuites=os.listdir(workspace+lower(country))
    print workspace+lower(country)
    testsuites.reverse()
    #print str(testsuites)
    for f in testsuites:
	#logger.info("testsuite file: "+f)
	#if f.find("nl")>0:
        #        continue
        f=f[:-4]
        print f
        #copyItem(f,"AE Regression Testing",region,country,f+"_Debug")
        #chain=f
        updateDescription("LQA Regression Testing",region,country,f)
	#break      
def UpdateAllDescriptionInview(viewURL):
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
    url="https://fusion.paypal.com/jenkins/j_acegi_security_check"
    json={"j_username": username, "j_password": password, "remember_me": "false", "from": ""}
    #res=s.post(url,data=json,verify=doVerify,proxies=None,cert=cert)
    res=s.post(url,data=json,verify=False)
    if(res.text.find('Invalid login information')>0):
        raise Exception("Failed to login")
    logger.info("user %s logged in successfully"%(username))
    #os.chdir(os.getcwd()+"\\..\\Localization\\localization-tests\\src\\test\\resources\\configfiles\\LqaRegressionTesting")
    #logger.info("Changed workdir to %s\\..\\Localization\\localization-tests\\src\\test\\resources\\configfiles\\LqaRegressionTesting"%(os.getcwd()))

##region="EMEA"
##country="Russia"
##language="ru"
##locale="RU"
##url="https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/LQA%20Regression%20Testing/view/EMEA/view/Russia/job/99_ruRU_ExpressCheckout/configure"
##def test():
##    s.get(url,cert=cert)
if __name__=='__main__':
    region="APAC"
    country="China_Localized"
    language="zh"
    locale="CN"
    login("kejiang","Symbio@2013")
    
    #UpdateAllDescriptionInview("https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/LQA%20Regression%20Testing/")
    UpdateAllDescriptionInview("https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/AE%20Regression%20Testing/")
    #UpdateAllDescriptionInview("https://fusion.paypal.com/jenkins/view/DEQualityAutomation/")
    #UpdateAllDescriptionInview("https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/%20New%20Regression/view/EMEA/view/Germany/")
    
