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


        self._setupColorManagement()

        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is not None:

            entity_name = self.context.entity['name']
            cameraColorspace, sequence = self._getCameraColorspaceAndSequence()

            os.environ["EVENT"] = str(entity_name)
            self.log_debug("Set environment variable 'EVENT' to %s" % entity_name)

            os.environ['SEQUENCE'] = str(sequence)
            self.log_debug("Set environment variable 'SEQUENCE' to %s" % sequence)

            os.environ['CAMERA'] = str(cameraColorspace)
            self.log_debug("Set environment variable 'CAMERA' to %s" % cameraColorspace)


        #refresh the color management to force a rebuild of the context
        cmds.colorManagementPrefs(refresh=True)


    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed.

        Donat note to self: I return False here, meaning that when the context changes
        > This app will be destroyed and reloaded, hence the new env vars will be evaluated
        """
        return False

    def destroy_app(self):
        """
        App teardown
        """
        self.log_debug("Destroying maya ocio app")



    ### private methods


    def _getCameraColorspaceAndSequence(self):

        tk = self.sgtk

        cameraColorspace = None
        sequence = None

        sg_filters = [["id", "is", self.context.entity["id"]]]  #  code of the current shot/asset
        sg_fields = ['sg_camera_colorspace', 'sg_review_colorspace', 'sg_sequence']
        data = tk.shotgun.find_one(self.context.entity["type"], filters=sg_filters, fields=sg_fields)
        if 'sg_camera_colorspace' in data:
            if data['sg_camera_colorspace']:
                cameraColorspace = data['sg_camera_colorspace']
        if 'sg_sequence' in data:
            if data['sg_sequence']:
                sequence = data['sg_sequence']['name']
        
        return cameraColorspace, sequence


    def _setupColorManagement(self):

        tk = self.sgtk

        self.logger.info("Enabling color management")
        cmds.colorManagementPrefs(e=True, cmEnabled=True) 

        if not 'ocio_config' in list(tk.templates.keys()):
            self.logger.error("Could not find ocio_config section in the shotguntemplates")
            return


        ocioSubPath = tk.templates['ocio_config'].definition   # Compositing\OCIO\config.ocio
        root = tk.roots['secondary']
        ocioPath = os.path.join(root, ocioSubPath)
        if os.path.isfile(ocioPath):
            ocioPath = ocioPath.replace(os.path.sep, "/") # for maya
            self.logger.info("Setting maya's ocio config to use : {}".format(ocioPath))
            cmds.colorManagementPrefs(e=True, configFilePath=ocioPath)
        else:
            self.logger.error("OCIO file {} is missing from disk".format(ocioPath))
            return
        
        # color managed pots :
        cmds.colorManagementPrefs(e=True, colorManagePots=True)

        color_rules = cmds.colorManagementFileRules(listRules=True)

        if "ColorSpaceNamePathSearch" not in color_rules:
            cmds.colorManagementFileRules(addRule="ColorSpaceNamePathSearch") # add that built in rule (bugs when cm prefs are open)

        # disable the 'Apply Output Transform to Renderer'
        cmds.colorManagementPrefs(e=True, outputTransformEnabled=False, outputTarget="renderer" )
