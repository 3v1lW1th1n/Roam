import os
import shutil
import random
import traceback

from datetime import datetime

from PyQt4.QtGui import QDialog, QFont, QColor, QIcon, QMessageBox, QStandardItem, QStandardItemModel, QInputDialog
from PyQt4.QtCore import QAbstractItemModel, QModelIndex, Qt


from configmanager.events import ConfigEvents

from configmanager.ui import ui_configmanager
import configmanager.logger as logger
from roam import resources_rc

import shutil
import roam.project
import roam.messagebaritems

from configmanager.ui.treenodes import *


class ConfigManagerDialog(ui_configmanager.Ui_ProjectInstallerDialog, QDialog):
    def __init__(self, roamapp, parent=None):
        super(ConfigManagerDialog, self).__init__(parent)
        self.setupUi(self)
        self.bar = roam.messagebaritems.MessageBar(self)

        self.roamapp = roamapp

        # Nope!
        self.projectwidget.roamapp = roamapp
        self.projectwidget.bar = self.bar

        self.treemodel = QStandardItemModel()
        self.projectList.setModel(self.treemodel)
        self.projectList.setHeaderHidden(True)

        self.projectList.selectionModel().currentChanged.connect(self.nodeselected)

        self.projectwidget.adjustSize()
        self.setWindowFlags(Qt.Window)

        self.projectwidget.projectupdated.connect(self.projectupdated)

        self.projectwidget.setaboutinfo()
        self.projectwidget.projects_page.projectlocationchanged.connect(self.loadprojects)
        self.setuprootitems()

        ConfigEvents.deleteForm.connect(self.delete_form)

    def raiseerror(self, *exinfo):
        self.bar.pushError(*exinfo)
        import roam.errors
        roam.errors.send_exception(exinfo)

    def setuprootitems(self):
        rootitem = self.treemodel.invisibleRootItem()
        self.roamnode = RoamNode()
        rootitem.appendRow(self.roamnode)

        self.projectsnode = ProjectsNode(folder=None)
        rootitem.appendRow(self.projectsnode)

        self.pluginsnode = PluginsNode()
        pluginpath = os.path.join(self.roamapp.apppath, "plugins")
        rootitem.appendRow(self.pluginsnode)
        self.pluginsnode.add_plugin_paths([pluginpath])

    def delete_form(self):
        index = self.projectList.currentIndex()
        node = index.data(Qt.UserRole)
        if not node.type() == Treenode.FormNode:
            return

        title, removemessage = node.removemessage
        delete = node.canremove
        if node.canremove and removemessage:
            button = QMessageBox.warning(self, title, removemessage, QMessageBox.Yes | QMessageBox.No)
            delete = button == QMessageBox.Yes

        print "Delete"
        if delete:
            parentindex = index.parent()
            newindex = self.treemodel.index(index.row(), 0, parentindex)
            if parentindex.isValid():
                parent = parentindex.data(Qt.UserRole)
                parent.delete(index.row())

            print parentindex
            self.projectList.setCurrentIndex(parentindex)

    def delete_project(self):
        index = self.projectList.currentIndex()
        node = index.data(Qt.UserRole)
        if node.type() == Treenode.ProjectNode:
            self.projectwidget._closeqgisproject()

        title, removemessage = node.removemessage
        delete = node.canremove
        if node.canremove and removemessage:
            button = QMessageBox.warning(self, title, removemessage, QMessageBox.Yes | QMessageBox.No)
            delete = button == QMessageBox.Yes

        if delete:
            parentindex = index.parent()
            newindex = self.treemodel.index(index.row(), 0, parentindex)
            if parentindex.isValid():
                parent = parentindex.data(Qt.UserRole)
                parent.delete(index.row())

            self.projectList.setCurrentIndex(newindex)

    def addprojectfolders(self, folders):
        self.projectwidget.projects_page.setprojectfolders(folders)

    def loadprojects(self, projectpath):
        projects = roam.project.getProjects([projectpath])
        self.projectsnode.loadprojects(projects, projectsbase=projectpath)

        index = self.treemodel.indexFromItem(self.projectsnode)
        self.projectList.setCurrentIndex(index)
        self.projectList.expand(index)

    def nodeselected(self, index, _):
        node = index.data(Qt.UserRole)
        if node is None:
            return

        project = node.project
        if project and not self.projectwidget.project == project:
            # Only load the project if it's different the current one.
            self.projectwidget.setproject(project)
            node.create_children()

            validateresults = list(project.validate())
            if validateresults:
                text = "Here are some reasons we found: \n\n"
                for message in validateresults:
                    text += "- {} \n".format(message)

                self.projectwidget.reasons_label.setText(text)

        if node.nodetype == Treenode.RoamNode:
            self.projectwidget.projectlabel.setText("IntraMaps Roam Config Manager")

        if node.nodetype == Treenode.AddNew:
            try:
                item = node.additem()
            except ValueError:
                return
            newindex = self.treemodel.indexFromItem(item)
            self.projectList.setCurrentIndex(newindex)
            return

        self.projectwidget.projectbuttonframe.setVisible(not project is None)
        self.projectwidget.setpage(node.page, node)

    def projectupdated(self):
        index = self.projectList.currentIndex()
        node = find_node(index)
        node.refresh()
