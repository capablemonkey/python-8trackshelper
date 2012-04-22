#-------------------------------------------------------------------------------
# Name:         8tracks Helper
# Purpose:      gets a list of your muziks
#
# Author:       capablemonkey (c) 2012
#
# Created:      12/17/2011
# Last Updated: 4/19/2012
#-------------------------------------------------------------------------------
#!/usr/bin/env python

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template

import os
import cgi
import urllib2
import string
import json
import urllib
import unicodedata
#import time

class homepage(webapp.RequestHandler):
    def get(self):
        # set path to template
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        # print out template
        self.response.out.write(template.render(path, 0))

class execute(webapp.RequestHandler):
    # requested username (global)
    username = ""

    # makes a log entry based on ActionLog model and pops it into the datastore
    def makelog(self, report):
        logging = self.ActionLog()
        logging.username = self.username[:50]
        logging.IP = self.request.remote_addr
        logging.success = report
        logging.put()

    # will be used later to keep track of how many requests served (fun facts)
    #class Stats(db.Model):
    #retrieved = db.IntegerProperty()

    # Models the log entry
    class ActionLog(db.Model):
        username = db.StringProperty()          # username requested
        IP = db.StringProperty()                # user's IP address
        time = db.DateTimeProperty(None, True)  # date + time of request
        success = db.BooleanProperty()          # whether or not the retrieval + presentation was successful

    # Handles post request
    def post(self):
        self.fetch_songs()
        return

    # main function to fetch songs
    def fetch_songs(self):
        # sets username by retrieving 'username' key from post request
        self.username = cgi.escape(self.request.get('username')).strip()

        # consolidation of all JSON pages
        consol = []

        # fetch up to 99 pages of favorited tracks
        for pagenum in range(0, 99):
            # construct URL
            url = "http://8tracks.com/users/" + self.username + "/favorite_tracks?page=" + str(pagenum) + "&per_page=20&format=jsonh"

            # try to fetch data for given username, but if 8tracks returns a
            # 404, this is most likely due to a bad username; so catch the
            # exception, yell at the user and do not proceed any further.
            try:
                req = urllib2.Request(url)
               	response = urllib2.urlopen(req)
            except:
                self.response.out.write('Invalid username :(')
                self.makelog(False)
                return

            # store this page of JSON data that we got back into gotten
            # gotten will later be appended to consol, this list of pages
            gotten = response.read()

        	# add page to consolidated total
            consol.append(gotten)

            # if it is revealed by the response from 8tracks.com that there is
            # no next page ("next_page":null), stop asking for the next page and break the loop
            if gotten.find('"next_page":null') > -1:
                break

        # try to parse the first page of data we got back.
        # this is to make sure it is indeed JSON and we can work with it
        try:
            k = json.JSONDecoder().decode(consol[0])
        # if this fails, there is probably a problem with the data we got, so
        # tell the user, log it, and exit
        except:
            self.response.out.write('something went wrong :(')
            self.makelog(False)
            return

        # if the data we get back indicates a 404, it's probably due to a bad username
        if k['status'] == "404 Not Found":
            self.response.out.write('Invalid username :(')
            self.makelog(False)
            return

        # string to store list of all tracks grabbed, to be put into table
        # using a template instead would be much cleaner and elegant!
        tracklist = ''

        # trackcount is used to produce the track numbers in the table
        trackcount = 1

        # print out header; a template should be used instead, but for now this will do
        self.response.out.write('<link rel="stylesheet" type="text/css" href="./static_files/style.css" /><center><a class="heading"><b class="user">' + self.username + '</b>\'s favorite tracks:</a> \n<table class="tracklist">')

        # for every page saved in the consol list, xml
        for xml in range(0, len(consol)):
            # decode the page
            k = json.JSONDecoder().decode(consol[xml])
            for tk in range(0, len(k["tracks"])):
                track = k["tracks"][tk]['performer'] + " - " + k["tracks"][tk]['name']
                tracklist = tracklist + track + '\n'
                #self.response.out.write(str(tk + 1) + '. ' + track + "<br>")

                yt = urllib.quote(track.encode('ascii', 'ignore'))
                # table row
                self.response.out.write('\n<tr><td>[' + str(trackcount) + ']</td><td><b>' + track + '</b></td><td><a href="http://www.youtube.com/results?search_query=' + yt +'"><img src="http://s.ytimg.com/yt/favicon-refresh-vfldLzJxy.ico" /></a></td><td><a href="http://grooveshark.com/#!/search?q=' + yt +'"><img src="http://grooveshark.com/webincludes/images/favicon.ico" /></a></td></tr>')
                trackcount += 1
        # footer
        self.response.out.write('</table><br><center><a class="heading">Plaintext:</a><br><textarea name="comments" cols="60" rows="10">' + tracklist + '</textarea></center><br><a href=".."><-- return</a>')
        # log transaction
        self.makelog(True)

application = webapp.WSGIApplication(
                                     [('/retrieve', execute),
                                     ('/.*', homepage)],
                                     debug=False)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()