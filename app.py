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


class mayaOCIO(Application):

    def init_app(self):
        """
        App entry point
        """
        self.log_debug("start maya ocio app")
        # make sure that the context has an entity associated - otherwise it wont work!

        if self.context.entity is not None:

            event = self.getEventName()
            cameraColorspace, sequence = self.getCameraColorspaceAndSequence()

            if event and not cameraColorspace:
              QtGui.QMessageBox.warning(None, 'OCIO Warning', "The camera colorspace of shot %s has not been defined.\nPlease go to our shotgun website and fill the camera colorspace field with the appropriate colorspace for this shot." % event)


            os.environ["EVENT"] = event
            self.log_debug("Set environment variable 'EVENT' to %s" % event)

            os.environ['SEQUENCE'] = sequence
            self.log_debug("Set environment variable 'SEQUENCE' to %s" % sequence)

            os.environ['CAMERA'] = cameraColorspace
            self.log_debug("Set environment variable 'CAMERA' to %s" % cameraColorspace)



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



    ###############################################################################################
    # implementation


    def getEventName(self):

        if self.context.entity["type"] == 'Shot':
            return self.context.entity['name']
        else: return None

    def getCameraColorspaceAndSequence(self):

        tk = self.sgtk

        cameraColorspace = None
        sequence = None

        if self.context.entity["type"] == 'Shot':
            self.log_debug("The context is 'Shot'")

            sg_filters = [["id", "is", self.context.entity["id"]]]  #  code of the current shot
            sg_fields = ['sg_camera_colorspace', 'sg_review_colorspace', 'sg_sequence']
            data = tk.shotgun.find_one(self.context.entity["type"], filters=sg_filters, fields=sg_fields)
            if 'sg_camera_colorspace' in data:
                if data['sg_camera_colorspace']:
                    cameraColorspace = data['sg_camera_colorspace']
            if 'sg_sequence' in data:
                if data['sg_sequence']:
                    sequence = data['sg_sequence']['name']
        
        return cameraColorspace, sequence