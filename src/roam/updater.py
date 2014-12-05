import functools
import os
import re
import zipfile
import urlparse
import urllib2

from collections import defaultdict
from PyQt4.QtNetwork import QNetworkRequest, QNetworkAccessManager
from PyQt4.QtCore import QObject, pyqtSignal, QUrl


def checkversion(toversion, fromversion):
    def versiontuple(v):
        v = v.split('.')[:3]
        version = tuple(map(int, (v)))
        if len(version) == 2:
            version = (version[0], version[1], 0)
        return version

    return versiontuple(toversion) > versiontuple(fromversion)


def parse_serverprojects(content):
    reg = 'href="(?P<file>(?P<name>\w+)-(?P<version>\d+(\.\d+)+).zip)"'
    versions = defaultdict(dict)
    for match in re.finditer(reg, content, re.I):
        version = match.group("version")
        path = match.group("file")
        name = match.group("name")
        data = dict(path=path,
                    version=version,
                    name=name)
        versions[name][version] = data
    return dict(versions)


def update_project(project, version, serverurl):
    if not serverurl:
        raise ValueError("No server url given")

    filename = "{}-{}.zip".format(project.basefolder, version)
    url = urlparse.urljoin(serverurl, "projects/{}".format(filename))
    content = urllib2.urlopen(url).read()
    rootfolder = os.path.join(project.folder, "..")
    tempfolder = os.path.join(rootfolder, "_updates")
    if not os.path.exists(tempfolder):
        os.mkdir(tempfolder)

    zippath = os.path.join(tempfolder, filename)
    with open(zippath, "wb") as f:
        f.write(content)

    with zipfile.ZipFile(zippath, "r") as z:
        z.extractall(rootfolder)

    project.projectUpdated.emit(project)


def get_project_info(projectname, projects):
    maxversion = max(projects[projectname])
    projectdata = projects[projectname][maxversion]
    return projectdata


def can_update(projectname, currentversion, projects):
    try:
        maxversion = max(projects[projectname])
        return checkversion(maxversion, currentversion)
    except KeyError:
        return False
    except ValueError:
        return False


def updateable_projects(projects, serverprojects):
    for project in projects:
        canupdate = can_update(project.basefolder, project.version, serverprojects)
        if canupdate:
            info = get_project_info(project.basefolder, serverprojects)
            yield project, info


class ProjectUpdater(QObject):
    """
    Object to handle reporting when new versions of projects are found on the update server.

    Emits foundProjects when a new projects are found
    """
    foundProjects = pyqtSignal(object)

    def __init__(self, server=None):
        super(ProjectUpdater, self).__init__()
        self.server = server
        self.net = QNetworkAccessManager()

    @property
    def projecturl(self):
        url = urlparse.urljoin(self.server, "projects/")
        return url

    def check_updates(self, server, installedprojects):
        if not server:
            return

        self.server = server
        req = QNetworkRequest(QUrl(self.projecturl))
        reply = self.net.get(req)
        reply.finished.connect(functools.partial(self.list_versions, reply, installedprojects))

    def update_server(self, newserverurl, installedprojects):
        self.check_updates(newserverurl, installedprojects)

    def list_versions(self, reply, installedprojects):
        content = reply.readAll().data()
        serverversions = parse_serverprojects(content)
        updateable = list(updateable_projects(installedprojects, serverversions))
        if updateable:
            self.foundProjects.emit(updateable)

    def update_project(self, project, version):
        update_project(project, version, self.server)



