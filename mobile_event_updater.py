#!/usr/bin/env python3

from kotlinswift_const_creator import convertToKotlinFile, convertToSwiftFile
import os
import shutil
import subprocess

className = "PredefinedEvents"

def exportFile(workingDirectory, eventsFilePath, classContent):
    open(eventsFilePath, "w").write(classContent)


def exportAndroid(eventsJson, androidProjectWorkingDirectory, androidProjectEventsFilePath):    
    kotlinFile = convertToKotlinFile(eventsJson, className)

    # Inserting kotlin class package definition
    kotlinFile = "package com.zoom.zoomtracker.analytics.model\n\n%s" % kotlinFile

    exportFile(
        workingDirectory= androidProjectWorkingDirectory,
        eventsFilePath= androidProjectEventsFilePath,
        classContent= kotlinFile
    )

def exportIOS(eventsJson, iOSProjectWorkingDirectory, iOSProjectEventsFilePath):            
    swiftFile = convertToSwiftFile(eventsJson, className)

    exportFile(
        workingDirectory= iOSProjectWorkingDirectory,
        eventsFilePath= iOSProjectEventsFilePath,
        classContent= swiftFile
    )


if __name__ == '__main__':
    currentPath = os.getcwd()

    eventsJson = open("mobile_events.json").read()

    exportIOS(
        eventsJson= eventsJson,
        iOSProjectWorkingDirectory = "../../ios/app-ios/",
        iOSProjectEventsFilePath = "../../ios/app-ios/Zoom/Zoom App/Zoom/PredefinedEvents.swift"
    )

    os.chdir(currentPath)    

    exportAndroid(
        eventsJson= eventsJson,
        androidProjectWorkingDirectory = "../../android/app-android/",
        androidProjectEventsFilePath = "../../android/app-android/ZoomAndroid/libraries/zoomtracker/src/main/java/com/zoom/zoomtracker/analytics/model/PredefinedEvents.kt"
    )

    os.chdir(currentPath)

    