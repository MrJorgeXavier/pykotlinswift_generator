#!/usr/bin/env python3

import os
from pydoc import classname
from pykotlinswift_const_creator import convertToKotlinFile, convertToSwiftFile
import sys


def exportFile(eventsFilePath, classContent):
    open(eventsFilePath, "w").write(classContent)


def exportAndroid(eventsJson, androidProjectEventsFilePath, className):    
    kotlinFile = convertToKotlinFile(eventsJson, className) 

    exportFile(
        eventsFilePath= androidProjectEventsFilePath,
        classContent= kotlinFile
    )

def exportIOS(eventsJson, iOSProjectEventsFilePath, className):            
    swiftFile = convertToSwiftFile(eventsJson, className)

    exportFile(
        eventsFilePath= iOSProjectEventsFilePath,
        classContent= swiftFile
    )


def export(args):
    if (len(args) == 0):
        raise(Exception("Missing arguments classname, json, iosfile and androidfile using the pattern <param>=<value> (Separating param name and value with an '=' without spaces.)"))        

    def getArgument(key):
        for arg in args:
            keyValue = arg.split("=")
            if (keyValue[0] == key):
                value = keyValue[1]
                if (value != None and len(value) > 0):
                    return value
        return None                        

    def getPathArgument(key):
        value = getArgument(key)
        
        if (value == None):
            return None

        if (os.path.exists(value)):
            return value
        
        raise(Exception("Param %s does not contain a valid file path" % key))
    
    jsonFilePath = getPathArgument("json")
    if (jsonFilePath == None):
        raise(Exception("Missing param 'json', please inform the json file containing the events to generate the code."))

    iosFilePath = getPathArgument("iosfile")
    if (iosFilePath == None):
        raise(Exception("Missing param 'iosfile', please inform the swift file to output the generated code."))

    androidFilePath = getPathArgument("androidfile")
    if (androidFilePath == None):
        raise(Exception("Missing param 'androidfile', please inform the kotlin file to output the generated code."))

    className = getArgument("classname")
    if (className == None):
        print("classname not specified, using 'HelloWorld' instead.")
        className = "HelloWorld"

    eventsJsonFile = open(jsonFilePath)
    eventsJson = eventsJsonFile.read()
    eventsJsonFile.close()

    exportIOS(
        eventsJson= eventsJson,
        iOSProjectEventsFilePath = iosFilePath,
        className = className
    )

    exportAndroid(
        eventsJson= eventsJson,
        androidProjectEventsFilePath = androidFilePath,
        className = className
    )

if __name__ == '__main__':
    args = sys.argv[1:]
    export(args)
    
    