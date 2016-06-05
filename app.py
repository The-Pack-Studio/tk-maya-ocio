# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
OCIO handling for Maya

"""

import sys
import os

from tank.platform import Application
from tank.platform.qt import QtCore, QtGui
import tank
import pymel.core as pm
import maya.cmds as cmds
from time import sleep

class mayaOCIO(Application):

    def init_app(self):
        """
        App entry point
        """
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the Maya OCIO application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")

        self.engine.register_command("Set OCIO for Arnold Render View", self.run_app)


    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed.
        """
        return True

    def destroy_app(self):
        """
        App teardown
        """
        self.log_debug("Destroying maya ocio app")

    def run_app(self):
        """
        Callback from when the menu is clicked.
        """
        
        event               = self.getEventName()
        cameraColorspace    = self.getCameraColorspace()
        OCIOConfigPath      = self.getOCIOConfigPath()

        if not OCIOConfigPath:
            QtGui.QMessageBox.warning(None, 'OCIO Warning', "Cannot find the ocio config file.\nIt is either missing from the template.yml or the file doesn't exist on disk")
            return

        if event and not cameraColorspace:
            QtGui.QMessageBox.warning(None, 'OCIO Warning', "The camera colorspace of shot %s has not been defined.\nPlease go to our shotgun website and fill the camera colorspace field with the appropriate colorspace for this shot." % event)
            return

        if not event:
            QtGui.QMessageBox.warning(None, 'OCIO Warning', "This is not a shot, so a general lut will be used for the 'GlobalView' view transform.\n The 'ShotView' view tranform will not work.")
            event = 'EV101'
            cameraColorspace = 'AlexaV3LogC'


        os.environ["EVENT"] = event
        self.log_debug("set environment variable 'EVENT' to %s" % event)

        
        os.environ['CAMERA'] = cameraColorspace
        self.log_debug("set environment variable 'CAMERA' to %s" % cameraColorspace)

        # first, clean OCIO settings in Arnold Render View

        cmds.arnoldRenderView( opt=( "LUT.OCIO", "0")  )
        cmds.arnoldRenderView( opt=("LUT.OCIO File", "" ))
        sleep(0.5)

        # now setting Arnold Render View to use OCIO, and setting the project's ocio config file path

        cmds.arnoldRenderView( opt=( "LUT.OCIO", "1")  )
        cmds.arnoldRenderView( opt=("LUT.OCIO File", OCIOConfigPath ))

        QtGui.QMessageBox.information(None, 'OCIO info', "OCIO settings have been set for shot %s which has a %s camera colorspace" % (event, cameraColorspace))
        # add a check to see if the EVxxx_Grade.cube or .3dl exist on disk and warn user of this.

    ###############################################################################################
    # implementation


    def getOCIOConfigPath(self):

        tk = self.sgtk

        if 'ocio_config' in tk.templates.keys():
            ocioSubPath = tk.templates['ocio_config'].definition   # should return Compositing\OCIO\config.ocio
            root = tk.roots['secondary']
            ocioPath = os.path.join(root, ocioSubPath)
            ocioPath = ocioPath.replace(os.path.sep, "/")
        else: return None
        
        if os.path.isfile(ocioPath):
            return ocioPath
        else: return None


    def getEventName(self):

        if self.context.entity["type"] == 'Shot':
            return self.context.entity['name']
        else: return None

    def getCameraColorspace(self):

        tk = self.sgtk

        if self.context.entity["type"] == 'Shot':
            self.log_debug("The context is 'Shot'")

            sg_filters = [["id", "is", self.context.entity["id"]]]  #  code of the current shot
            sg_fields = ['sg_camera_colorspace', 'sg_review_colorspace']
            data = tk.shotgun.find_one(self.context.entity["type"], filters=sg_filters, fields=sg_fields)
            if 'sg_camera_colorspace' in data:
                if data['sg_camera_colorspace'] is not None:
                    return data['sg_camera_colorspace']
        return None