#!/usr/bin/env python
"""Spider to try and find bugs in the parser. Requires httplib2 and elementtree.

usage:
import spider
s = spider.Spider()
s.spider("http://www.google.com", maxURLs=100)
"""
from __future__ import absolute_import, division, unicode_literals, print_function

import sys

try:
    import urllib.parse as urllib_parse
except ImportError:
    import urlparse as urllib_parse
try:
    import urllib.robotparser as robotparser
except ImportError:
    import robotparser

from hashlib import md5

import httplib2
import html5lib


class Spider(object):

    def __init__(self):
        self.unvisitedURLs = set()
        self.visitedURLs = set()
        self.buggyURLs = set()
        self.robotParser = robotparser.RobotFileParser()
        self.contentDigest = {}
        self.http = httplib2.Http(".cache")

    def run(self, initialURL, maxURLs=1000):
        urlNumber = 0
        self.visitedURLs.add(initialURL)
        content = self.loadURL(initialURL)
        while maxURLs is None or urlNumber < maxURLs:
            if content is not None:
                self.parse(content)
                urlNumber += 1
            if not self.unvisitedURLs:
                break
            content = self.loadURL(self.unvisitedURLs.pop())
        return urlNumber

    def parse(self, content):
        failed = False
        p = html5lib.HTMLParser(tree=html5lib.getTreeBuilder('etree'))
        try:
            tree = p.parse(content)
        except Exception as e:
            self.buggyURLs.add(self.currentURL)
            failed = True
            print("BUGGY: {0}: {1}".format(self.currentURL, e), file=sys.stderr)
        self.visitedURLs.add(self.currentURL)
        if not failed:
            self.updateURLs(tree)

    def loadURL(self, url):
        print('Processing {0}'.format(url), file=sys.stderr)
        try:
            resp, content = self.http.request(url, "GET")
        except Exception as e:
            print("Failed to fetch {0}: {1}".format(url, e), file=sys.stderr)
            return None

        self.currentURL = url
        digest = md5(content).hexdigest()
        if digest in self.contentDigest:
            content = None
            self.visitedURLs.add(url)
        else:
            self.contentDigest[digest] = url

        if resp['status'] not in ('200', '304'):
            print("Fetch {0} status {1}".format(url, resp['status']), file=sys.stderr)
            content = None

        return content

    def updateURLs(self, tree):
        """Take all the links in the current document, extract the URLs and
        update the list of visited and unvisited URLs according to whether we
        have seen them before or not"""
        urls = set()
        # Remove all links we have already visited
        namespace = tree.tag[1:].split('}')[0]
        links = list(tree.findall('.//{%s}a' % namespace))
        for link in links:
            try:
                url = urllib_parse.urldefrag(link.attrib['href'])[0]
                if (url and url not in self.unvisitedURLs and url
                        not in self.visitedURLs):
                    urls.add(url)
            except KeyError:
                pass

        # Remove all non-http URLs and add a suitable base URL where that is
        # missing
        newUrls = set()
        for url in urls:
            splitURL = list(urllib_parse.urlsplit(url))
            if splitURL[0] != "http":
                continue
            if splitURL[1] == "":
                splitURL[1] = urllib_parse.urlsplit(self.currentURL)[1]
            newUrls.add(urllib_parse.urlunsplit(splitURL))
        urls = newUrls

        responseHeaders = {}
        # Now we want to find the content types of the links we haven't visited
        for url in urls:
            print('Checking {0}'.format(url), file=sys.stderr)
            try:
                resp, content = self.http.request(url, "HEAD")
                responseHeaders[url] = resp
            except Exception as e:
                print('Error fetching HEAD of {0}: {1}'.format(url, e), file=sys.stderr)

        # Remove links not of content-type html or pages not found
        # XXX - need to deal with other status codes?
        toVisit = set([url for url in urls if url in responseHeaders and
                       'html' in responseHeaders[url].get('content-type', '') and
                       responseHeaders[url]['status'] == "200"])

        # Now check we are allowed to spider the page
        for url in list(toVisit):
            robotURL = list(urllib_parse.urlsplit(url)[:2])
            robotURL.extend(["robots.txt", "", ""])
            robotURL = urllib_parse.urlunsplit(robotURL)
            self.robotParser.set_url(robotURL)
            try:
                self.robotParser.read()
            except Exception as e:
                print('Failed to read {0}: {1}'.format(robotURL, e), file=sys.stderr)
                toVisit.remove(url)
                continue

            if not self.robotParser.can_fetch("*", url):
                print('{0} rejects {1}'.format(robotURL, url), file=sys.stderr)
                toVisit.remove(url)

        self.visitedURLs.update(urls)
        self.unvisitedURLs.update(toVisit)


def main():
    max_urls = 100
    s = Spider()
    count = s.run("http://yahoo.com/", maxURLs=max_urls)
    if s.buggyURLs:
        print('Buggy URLs:')
        print('  ' + '\n  '.join(s.buggyURLs))
        print('')
    if count != max_urls:
        print('{0} of {1} processed'.format(count, max_urls))
    sys.exit(count == max_urls and len(s.buggyURLs) == 0)

if __name__ == '__main__':
    main()
