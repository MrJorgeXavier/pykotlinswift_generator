#!/usr/bin/env python3

import os
from kotlinswift_const_creator import convertToKotlinFile, convertToSwiftFile
import sys

className = "PredefinedEvents"

def exportFile(eventsFilePath, classContent):
    open(eventsFilePath, "w").write(classContent)


def exportAndroid(eventsJson, androidProjectEventsFilePath):    
    kotlinFile = convertToKotlinFile(eventsJson, className)

    # Inserting kotlin class package definition
    kotlinFile = "package com.zoom.zoomtracker.analytics.model\n\n%s" % kotlinFile

    exportFile(
        eventsFilePath= androidProjectEventsFilePath,
        classContent= kotlinFile
    )

def exportIOS(eventsJson, iOSProjectEventsFilePath):            
    swiftFile = convertToSwiftFile(eventsJson, className)

    exportFile(
        eventsFilePath= iOSProjectEventsFilePath,
        classContent= swiftFile
    )


def export(args):
    if (len(args) == 0):
        raise(Exception("Missing arguments json, iosfile and androidfile using the pattern <param>=<value> (Separating param name and value with an '=' without spaces.)"))        

    def getPathArgument(key):
        for arg in args:
            keyValue = arg.split("=")
            if (keyValue[0] == key):
                value = keyValue[1]
                if (os.path.exists(value)):
                    return value
                else:
                    raise(Exception("Param %s does not contain a valid file path" % key))
        return None                        
    
    jsonFilePath = getPathArgument("json")
    if (jsonFilePath == None):
        raise(Exception("Missing param 'json', please inform the json file containing the events to generate the code."))

    iosFilePath = getPathArgument("iosfile")
    if (iosFilePath == None):
        raise(Exception("Missing param 'iosfile', please inform the swift file to output the generated code."))

    androidFilePath = getPathArgument("androidfile")
    if (androidFilePath == None):
        raise(Exception("Missing param 'androidfile', please inform the kotlin file to output the generated code."))

    eventsJson = open(jsonFilePath).read()

    exportIOS(
        eventsJson= eventsJson,
        iOSProjectEventsFilePath = iosFilePath
    )

    exportAndroid(
        eventsJson= eventsJson,
        androidProjectEventsFilePath = androidFilePath
    )

if __name__ == '__main__':
    args = sys.argv[1:]
    export(args)
    
    