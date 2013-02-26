# -*- coding: utf-8 -*-
import os
from string import *
import logging,requests
from urllib import *
from urlparse import *

s=requests.Session()
jenkinsBaseURL = "https://fusion.paypal.com/jenkins/"
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
def copyView(srcviewurl,dstviewurl,suffix):
	api_url = urljoin(srcviewurl,"/api/python?depth=2")
	r = s.get(api_url)
	srcdict = eval(r.text)
	api_url = urljoin(dstviewurl,"/api/python?depth=2")
	r = s.get(api_url)
	dstdict = eval(r.text)
	copysubview(srcdict,dstdict)

def copysubview(srcdict,dstdict):
	for view in srcdict['views']:
		copysubview(view)
	for job in dstdict['jobs']:
		pass
def copyjob():
	pass

def crateview():
	pass

def deleteItem(region,country,testsuite,chain):
	logger.info("Update test suite %s %s %s %s"%(region,country,testsuite,chain))
	url="https://fusion.paypal.com/jenkins/view/InternationalQA_View/view/%s/view/%s/view/%s/job/%s/doDelete"%(quote("LQA Regression Testing"),region,country,testsuite)
	logger.info(url)
	data={"Submit":"Yes",json:{}}
	res=s.post(url,data=data)
def updateDescription(joburl):
    logger.info("Update test suite %s"%(joburl))
    url1=joburl+"description"
    desc="<br><br><a style=\"color:blue\" href=\"%sws/target/surefire-reports/html/report.html\"><font size =4>Bluefin HTML Report </font></a>"%(joburl)
    json = {"description":desc}
    res=s.post(url2,data=json)
    if res.status_code !=200:
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
def main(region,country):
    logger.info("current workspace: "+os.getcwd())
    if(not os.path.exists(workspace+lower(country))):
        os.makedirs(workspace+lower(country))
    chain=""
    testsuites=os.listdir(workspace+lower(country))
    print lower(country)
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
	#break      
def login(username,password):
    url=baseURL+"j_acegi_security_check"
    json={"j_username": username, "j_password": password, "remember_me": "false", "from": ""}

    #res=s.post(url,data=json,verify=doVerify,proxies=None,cert=cert)
    res=s.post(url,data=json,verify=False)
    if(not res.text.find('<a href="/jenkins/logout"><b>log out</b></a>')):
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
	if len(sys.argv) !=3:
		return
	login("kejiang","Symbio@2013")
	main(sys.argv[1],sys.argv[2])

    
