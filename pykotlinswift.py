#!/usr/bin/env python3

import os
import json
from pykotlinswift_const_creator import convertToKotlinFile, convertToSwiftFile, raiseException
import sys


def exportFile(eventsFilePath, classContent):
    open(eventsFilePath, "w").write(classContent)


def exportAndroid(eventsJson, androidProjectEventsFilePath, className, version):    
    kotlinFile = convertToKotlinFile(eventsJson, className, version) 

    exportFile(
        eventsFilePath= androidProjectEventsFilePath,
        classContent= kotlinFile
    )

def exportIOS(eventsJson, iOSProjectEventsFilePath, className, version):            
    swiftFile = convertToSwiftFile(eventsJson, className, version)

    exportFile(
        eventsFilePath= iOSProjectEventsFilePath,
        classContent= swiftFile
    )

def export(jsonFilePath, iosFilePath, androidFilePath, className, androidClassPackage, version):
    eventsJsonFile = open(jsonFilePath)
    eventsJson = eventsJsonFile.read()
    eventsJsonFile.close()

    exportIOS(
        eventsJson= eventsJson,
        iOSProjectEventsFilePath = iosFilePath,
        className = className,
        version = version
    )

    exportAndroid(
        eventsJson= eventsJson,
        androidProjectEventsFilePath = androidFilePath,
        className = className,
        version = version
    )

    # Inserting zoom kotlin class package definition
    kotlinFile = open(androidFilePath, "r")
    kotlinFileContent = "%s\n\n%s" % (androidClassPackage, kotlinFile.read())
    kotlinFile.close()
    kotlinFile = open(androidFilePath, "w")
    kotlinFile.write(kotlinFileContent)
    kotlinFile.close()    

def getArgument(key, args):
        for arg in args:
            keyValue = arg.split("=")
            if (keyValue[0] == key):
                value = keyValue[1]
                if (value != None and len(value) > 0):
                    return value
        return None

def getPathArgument(key, args):
        value = getArgument(key, args)
        
        if (value == None):
            return None

        if (os.path.exists(value)):
            return value
        
        raiseException("Param %s does not contain a valid file path" % key)

def exportFromArgs(args):
    if (len(args) == 0):
        raiseException("Missing arguments classname, json, iosfile and androidfile using the pattern <param>=<value> (Separating param name and value with an '=' without spaces.)")

    def getArgument(key):
        return getArgument(key, args)

    def getPathArgument(key):
        return getPathArgument(key, args)
    
    jsonFilePath = getPathArgument("json")
    if (jsonFilePath == None):
        raiseException("Missing param 'json', please inform the json file containing the events to generate the code.")

    iosFilePath = getPathArgument("iosfile")
    if (iosFilePath == None):
        raiseException("Missing param 'iosfile', please inform the swift file to output the generated code.")

    androidFilePath = getPathArgument("androidfile")
    if (androidFilePath == None):
        raiseException("Missing param 'androidfile', please inform the kotlin file to output the generated code.")

    className = getArgument("classname")
    if (className == None):
        print("classname not specified, using 'HelloWorld' instead.")
        className = "HelloWorld"

    androidClassPackage = getArgument("androidpackage")    
    if (androidClassPackage == None):
        print("androidpackage not specified, which will cause problems to be imported by other classes in the project")
        androidClassPackage = "// package not specified in the pykotlinswift call"
    else:
        androidClassPackage = "package %s" % androidClassPackage

    export(
        jsonFilePath=jsonFilePath,
        iosFilePath=iosFilePath,
        androidFilePath=androidFilePath,
        className=className,
        androidClassPackage=androidClassPackage,
        version=getArgument("version")
    )

def exportFromSettingsFile(settingsFilePath):
    settingsJsonFile = open(settingsFilePath)
    settingsObject = json.loads(settingsJsonFile.read())
    settingsJsonFile.close()

    export(
        jsonFilePath=settingsObject["_jsonTemplateFilePath"],
        iosFilePath=settingsObject["_iosOutputFilePath"],
        androidFilePath=settingsObject["_androidOutputFilePath"],
        className=settingsObject["_rootClassName"],
        androidClassPackage=settingsObject["_androidClassPackage"],
        version=settingsObject["_version"]
    )
    
    
if __name__ == '__main__':
    args = sys.argv[1:]
    jsonSettingsPath = getPathArgument("settings", args)
    if jsonSettingsPath != None:
        exportFromSettingsFile(jsonSettingsPath)
    else:
        exportFromArgs(args)
    
    