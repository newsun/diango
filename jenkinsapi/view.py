from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.job import Job
import urllib

class View(JenkinsBase):

    def __init__(self, url, name, jenkins_obj):
        self.name = name
        self.jenkins_obj = jenkins_obj
        JenkinsBase.__init__(self, url)

    def __str__(self):
        return self.name
    
    ################ Job Api Part I ######################
    
    def __getitem__(self, str_job_id ):
        assert isinstance( str_job_id, str )
        api_url = self.python_api_url( self.get_job_url( str_job_id ) )
        return Job( api_url, str_job_id, self.jenkins_obj )

    def keys(self):
        return self.get_job_dict().keys()

    def iteritems(self):
        for name, url in self.get_job_dict().iteritems():
            api_url = self.python_api_url( url )
            yield name, Job( api_url, name, self.jenkins_obj )

    def values(self):
        return [ a[1] for a in self.iteritems() ]

    def items(self):
        return [ a for a in self.iteritems() ]

    def _get_jobs( self ):
        if not self._data.has_key( "jobs" ):
            pass
        else:
            for viewdict in self._data["jobs"]:
                yield viewdict["name"], viewdict["url"]

    def get_job_dict(self):
        return dict( self._get_jobs() )

    def __len__(self):
        return len( self.get_job_dict().keys() )

    def get_job_url( self, str_job_name ):
        try:
            job_dict = self.get_job_dict()
            return job_dict[ str_job_name ]
        except KeyError:
            #noinspection PyUnboundLocalVariable
            all_views = ", ".join( job_dict.keys() )
            raise KeyError("Job %s is not known - available: %s" % ( str_job_name, all_views ) )

    def get_jenkins_obj(self):
        return self.jenkins_obj

    def add_job(self, str_job_name):
        if str_job_name in self.get_job_dict():
            return "Job %s has in View %s" %(str_job_name, self.name)
        elif not self.get_jenkins_obj().has_job(str_job_name):
            return "Job %s is not known - available: %s" % ( str_job_name, ", ".join(self.get_jenkins_obj().get_jobs_list()))
        else:
            data = {
                "description":"",
                "statusFilter":"",
                "useincluderegex":"on",
                "includeRegex":"",
                "columns": [{"stapler-class": "hudson.views.StatusColumn", "kind": "hudson.views.StatusColumn"}, 
                            {"stapler-class": "hudson.views.WeatherColumn", "kind": "hudson.views.WeatherColumn"}, 
                            {"stapler-class": "hudson.views.JobColumn", "kind": "hudson.views.JobColumn"}, 
                            {"stapler-class": "hudson.views.LastSuccessColumn", "kind": "hudson.views.LastSuccessColumn"}, 
                            {"stapler-class": "hudson.views.LastFailureColumn", "kind": "hudson.views.LastFailureColumn"}, 
                            {"stapler-class": "hudson.views.LastDurationColumn", "kind": "hudson.views.LastDurationColumn"}, 
                            {"stapler-class": "hudson.views.BuildButtonColumn", "kind": "hudson.views.BuildButtonColumn"}],
                "Submit":"OK",
                }
            data["name"] = self.name
            for job in self.get_job_dict().keys():
                data[job]='on'
            data[str_job_name] = "on"
            data['json'] = data.copy()
            self.post_data('%sconfigSubmit' % self.baseurl, urllib.urlencode(data))
            return "Job %s is add in View %s successful" % (str_job_name, self.baseurl)

    def id(self):
        """
        Calculate an ID for this object.
        """
        return "%s.%s" % ( self.className, self.name )
    
    ###################### Job Api Part II ###################
    
#    def get_jobs(self):
#        """
#        Fetch all the build-names on this Jenkins server.
#        """
#        for info in self._data["jobs"]:
#            yield info["name"], Job(info["url"], info["name"], jenkins_obj=self)

#    def get_jobs_info(self):
#        """
#        Get the jobs information
#        :return url, name
#        """
#        for info in self._data["jobs"]:
#            yield info["url"], info["name"]

    def get_jobs_list(self):
        """
        return jobs dict,'name:url'
        """
        jobs = []
        for info in self._data["jobs"]:
            jobs.append(info["name"])
        return jobs

    def get_job(self, jobname):
        """
        Get a job by name
        :param jobname: name of the job, str
        :return: Job obj
        """
        return self[jobname]

    def has_job(self, jobname):
        """
        Does a job by the name specified exist
        :param jobname: string
        :return: boolean
        """
        return jobname in self.get_jobs_list()

    def create_job(self, jobname, config):
        """
        Create a job
        :param jobname: name of new job, str
        :param config: configuration of new job, xml
        :return: new Job obj
        """
        headers = {'Content-Type': 'text/xml'}
        qs = urllib.urlencode({'name': jobname})
        url = urlparse.urljoin(self.baseurl, "createItem?%s" % qs)
        request = urllib2.Request(url, config, headers)
        self.post_data(request, None)
        newjk = self._clone()
        return newjk.get_job(jobname)

    def copy_job(self, jobname, newjobname):
        """
        Copy a job
        :param jobname: name of a exist job, str
        :param newjobname: name of new job, str
        :return: new Job obj
        """
        qs = urllib.urlencode({'name': newjobname,
                               'mode': 'copy',
                               'from': jobname})
        copy_job_url = urlparse.urljoin(self.baseurl, "createItem?%s" % qs)
        self.post_data(copy_job_url, '')
        newjk = self._clone()
        return newjk.get_job(newjobname)

    def delete_job(self, jobname):
        """
        Delete a job by name
        :param jobname: name of a exist job, str
        :return: new jenkins_obj
        """
        delete_job_url = urlparse.urljoin(self._clone().get_job(jobname).baseurl, "doDelete" )
        self.post_data(delete_job_url, '')
        newjk = self._clone()
        return newjk

    def rename_job(self, jobname, newjobname):
        """
        Rename a job
        :param jobname: name of a exist job, str
        :param newjobname: name of new job, str
        :return: new Job obj
        """
        qs = urllib.urlencode({'newName': newjobname})
        rename_job_url = urlparse.urljoin(self._clone().get_job(jobname).baseurl, "doRename?%s" % qs)
        self.post_data(rename_job_url, '')
        newjk = self._clone()
        return newjk.get_job(newjobname)
#
#    def iteritems(self):
#        return self.get_jobs()

    def iterkeys(self):
        for info in self._data["jobs"]:
            yield info["name"]

#    def keys(self):
#        return [ a for a in self.iterkeys() ]

    ###################### View Api ##########################
    
    def _get_views(self):
        if not self._data.has_key("views"):
            pass
        else:
            for viewdict in self._data["views"]:
                yield viewdict["name"], viewdict["url"]

    def get_view_dict(self):
        return dict(self._get_views())

    def get_view_url(self, str_view_name):
        try:
            view_dict = self.get_view_dict()
            return view_dict[ str_view_name ]
        except KeyError:
            #noinspection PyUnboundLocalVariable
            all_views = ", ".join(view_dict.keys())
            raise KeyError("View %s is not known - available: %s" % (str_view_name, all_views))

    def get_view(self, str_view_name):
        view_url = self.get_view_url(str_view_name)
        view_api_url = self.python_api_url(view_url)
        return View(view_url , str_view_name, jenkins_obj=self)

    def get_view_by_url(self, str_view_url):
        #for nested view
        str_view_name = str_view_url.split('/view/')[-1].replace('/', '')
        return View(str_view_url , str_view_name, jenkins_obj=self)

    def delete_view_by_url(self, str_url):
        url = "%s/doDelete" %str_url
        self.post_data(url, '')
        newjk = self._clone()
        return newjk
    
    def has_view(self,view_name):
        return view_name in self.get_view_dict()
    
    def create_view(self, str_view_name, people=None):
        """
        Create a view, viewExistsCheck
        :param str_view_name: name of new view, str
        :return: new view obj
        """
        url = urlparse.urljoin(self.baseurl, "user/%s/my-views/" % people) if people else self.baseurl
        qs = urllib.urlencode({'value': str_view_name})
        viewExistsCheck_url = urlparse.urljoin(url, "viewExistsCheck?%s" % qs)
        fn_urlopen = self.get_jenkins_obj().get_opener()
        try:
            r = fn_urlopen(viewExistsCheck_url).read()
        except urllib2.HTTPError, e:
            log.debug("Error reading %s" % viewExistsCheck_url)
            log.exception(e)
            raise
        """<div/>"""
        if len(r) > 7: 
            return 'A view already exists with the name "%s"' % (str_view_name)
        else:
            data = {"mode":"hudson.model.ListView", "Submit": "OK"}
            data['name']=str_view_name
            data['json'] = data.copy()
            params = urllib.urlencode(data)
            try:
                createView_url = urlparse.urljoin(url, "createView")
                result = self.post_data(createView_url, params)
            except urllib2.HTTPError, e:
                log.debug("Error post_data %s" % createView_url)
                log.exception(e)
            return urlparse.urljoin(url, "view/%s/" % str_view_name)

    def __getitem__(self, str_job_id ):
        assert isinstance( str_job_id, str )
        api_url = self.python_api_url( self.get_job_url( str_job_id ) )
        return Job( api_url, str_job_id, self.jenkins_obj )

    def keys(self):
        return self.get_job_dict().keys()

    def iteritems(self):
        for name, url in self.get_job_dict().iteritems():
            api_url = self.python_api_url( url )
            yield name, Job( api_url, name, self.jenkins_obj )

    def values(self):
        return [ a[1] for a in self.iteritems() ]

    def items(self):
        return [ a for a in self.iteritems() ]

    def _get_jobs( self ):
        if not self._data.has_key( "jobs" ):
            pass
        else:
            for viewdict in self._data["jobs"]:
                yield viewdict["name"], viewdict["url"]

    def get_job_dict(self):
        return dict( self._get_jobs() )

    def __len__(self):
        return len( self.get_job_dict().keys() )

    def get_job_url( self, str_job_name ):
        try:
            job_dict = self.get_job_dict()
            return job_dict[ str_job_name ]
        except KeyError:
            #noinspection PyUnboundLocalVariable
            all_views = ", ".join( job_dict.keys() )
            raise KeyError("Job %s is not known - available: %s" % ( str_job_name, all_views ) )

    def get_jenkins_obj(self):
        return self.jenkins_obj

    def add_job(self, str_job_name):
        if str_job_name in self.get_job_dict():
            return "Job %s has in View %s" %(str_job_name, self.name)
        elif not self.get_jenkins_obj().has_job(str_job_name):
            return "Job %s is not known - available: %s" % ( str_job_name, ", ".join(self.get_jenkins_obj().get_jobs_list()))
        else:
            data = {
                "description":"",
                "statusFilter":"",
                "useincluderegex":"on",
                "includeRegex":"",
                "columns": [{"stapler-class": "hudson.views.StatusColumn", "kind": "hudson.views.StatusColumn"}, 
                            {"stapler-class": "hudson.views.WeatherColumn", "kind": "hudson.views.WeatherColumn"}, 
                            {"stapler-class": "hudson.views.JobColumn", "kind": "hudson.views.JobColumn"}, 
                            {"stapler-class": "hudson.views.LastSuccessColumn", "kind": "hudson.views.LastSuccessColumn"}, 
                            {"stapler-class": "hudson.views.LastFailureColumn", "kind": "hudson.views.LastFailureColumn"}, 
                            {"stapler-class": "hudson.views.LastDurationColumn", "kind": "hudson.views.LastDurationColumn"}, 
                            {"stapler-class": "hudson.views.BuildButtonColumn", "kind": "hudson.views.BuildButtonColumn"}],
                "Submit":"OK",
                }
            data["name"] = self.name
            for job in self.get_job_dict().keys():
                data[job]='on'
            data[str_job_name] = "on"
            data['json'] = data.copy()
            self.post_data('%sconfigSubmit' % self.baseurl, urllib.urlencode(data))
            return "Job %s is add in View %s successful" % (str_job_name, self.baseurl)

    def id(self):
        """
        Calculate an ID for this object.
        """
        return "%s.%s" % ( self.className, self.name )
