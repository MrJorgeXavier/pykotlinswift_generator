#!/usr/bin/env python3

import json
import re

## 
## PARSING DICTIONARY TO LANGUAGE INSTRUCTIONS LOGIC:
##
class CodeClass:
    def __init__(self, indentationCharacter, language, constKeyword):
        self.indentationCharacter = indentationCharacter
        self.language = language
        self.constKeyword = constKeyword
        self.indentationLevel = 0
        self.name = "Unknown"
        self.innerClasses = []
        self.methodProperties = []
        self.attributeLines = []

    def createInnerClass(self):
        return None

    def createClassDefinition(self):
        return None

    def createStringInterpolatedValue(self, value):
        return None
    
    def createParamName(self, name, type, userDefined):
        return None

    def createEventClassDefinition(self):
        return None

    def createMapDefinition(self, values):
        return None

    def createEventClassInstance(self, name, value):
        return None

    def createMapDefinition(self, values):
        params = ""
        for valueKey in values:
            value = values[valueKey]
            
            if (len(params) > 0):
                    params += ", "

            if (isinstance(value, str)):
                if ("%" in value):                
                    params += "%s = %s" % (valueKey, self.createStringInterpolatedValue(valueKey))
                else:
                    params += "%s = \"%s\"" % (valueKey, value)
            elif (isinstance(value, float)):
                params += "%s %s = %.2f" % (self.constKeyword, valueKey, value)
            elif (isinstance(value, int)):
                params += "%s %s = %d" % (self.constKeyword, valueKey, value)            
            elif (isinstance(value, list)):
                raise(Exception("Arrays are not supported! Use only strings, floats, ints and objects."))            
        return params

    def createEventMethodDefinition(self, methodName, eventName, eventParams):
        methodArguments = ""
        methodReturnValue = ""
        
        for paramName in eventParams:
            paramValue = eventParams[paramName]
            
            if ("%" in paramValue):
                # Define type of param
                typeChar = re.findall("%.", paramValue)[0]
                
                paramType = ""
                if ("d" in typeChar):
                    paramType = "Int"
                elif ("f" in typeChar):
                    paramType = "Float"
                elif ("s" in typeChar):
                    paramType = "String"
                
                # Write arguments
                if (len(methodArguments) > 0):
                    methodArguments = "%s, " % (methodArguments)

                methodArguments = "%s%s" % (methodArguments, self.createParamName(paramName, paramType, True))                                
                continue

        # Write return value
        mapParams = self.createMapDefinition(eventParams)
        methodReturnValue = "return %s" % (self.createEventClassInstance(eventName, mapParams))

        return (methodName, methodArguments, methodReturnValue)


    def parseClassObject(self, jsonObject):
        properties = jsonObject

        for key in properties:
            value = properties[key]
            if (isinstance(value, str)):
                if "%" in value:
                    methodLines = self.createMethodDefinition(key, value)
                    self.methodProperties.append(methodLines)
                else:
                    self.attributeLines.append(("%s %s = \"%s\"" % (self.constKeyword, key, value)))
            elif (isinstance(value, float)):
                self.attributeLines.append(("%s %s = %.2f" % (self.constKeyword, key, value)))
            elif (isinstance(value, int)):
                self.attributeLines.append(("%s %s = %d" % (self.constKeyword, key, value)))
            elif (isinstance(value, list)):
                raise(Exception("Arrays are not supported! Use only strings, floats, ints and objects."))
            elif (isinstance(value, object)):
                if value["_name"] != None:
                    methodName = key
                    eventName = value["_name"]
                    eventParams = value["_params"]
                    eventMethodLines = self.createEventMethodDefinition(methodName, eventName, eventParams)
                    self.methodProperties.append(eventMethodLines)
                else:  
                    innerClass = self.createInnerClass()
                    innerClass.name = key
                    innerClass.indentationLevel = self.indentationLevel + 1
                    innerClass.parseClassObject(value)
                    self.innerClasses.append(innerClass)

    def indentation(self, level):
            ident = ""
            for i in range(0,level):
                ident = "%s%s" % (ident, self.indentationCharacter)
            return ident
    
    def generateClassDefinitionLines(self):
        lines = []
        
        def writeLine(line, level):
            lines.append("%s%s" % (self.indentation(level), line))

        writeLine(self.createClassDefinition(), self.indentationLevel)
        
        for attributeLine in self.attributeLines:
            writeLine(attributeLine, self.indentationLevel + 1)

        if (len(self.methodProperties) > 0):
            writeLine("", self.indentationLevel)
        
        for method in self.methodProperties:
            writeLine(method[0], self.indentationLevel + 1)
            for line in range(1, len(method) - 1):
                writeLine(method[line], self.indentationLevel + 2)
            writeLine(method[-1], self.indentationLevel + 1)

        if (len(self.innerClasses) > 0):
            writeLine("", self.indentationLevel)
            writeLine("", self.indentationLevel)

        for innerClass in self.innerClasses:
            innerClassLines = innerClass.generateClassDefinitionLines()
            for innerClassLine in innerClassLines:
                writeLine(innerClassLine, self.indentationLevel)
                    
        writeLine("}", self.indentationLevel)
        
        return lines

class KotlinClass(CodeClass):    
    def __init__(self):
        super().__init__(
            indentationCharacter="    ",
            language= "Kotlin",
            constKeyword= "const val"
        )
    
    def createInnerClass(self):
        return KotlinClass()

    def createClassDefinition(self):        
        return "object %s {" % self.name

    def createStringInterpolatedValue(self, value):
        return "${%s}" % value

    def createParamName(self, name, type, userDefined):
        return "%s: %s" % (name, type)

    def createMethodDefinition(self, name, value):
        methodProps = super().createMethodDefinition(name, value)
        return [
            "fun %s(%s): String {" % (methodProps[0], methodProps[1]),
            "return \"%s\"" % (methodProps[2]),
            "}"
        ]
    
    def createEventClassDefinition(self):
        return [
            "data class EventData(val name: String, val params: Map<String, Any>)"
        ]

    def createEventClassInstance(self, name, value):
        return "EventData(%s, %s)" % (name, value)

    def createMapDefinition(self, values):
        mapValues = super().createMapDefinition(values)
        return "mapOf(%s)" % (mapValues.replace("="," to "))
                

class SwiftClass(CodeClass):    
    def __init__(self):
        super().__init__(
            indentationCharacter="    ",
            language= "Swift",
            constKeyword= "static let"
        )
    
    def createInnerClass(self):
        return SwiftClass()

    def createClassDefinition(self):        
        return "struct %s {\n%sprivate init() {}\n" % (self.name, self.indentation(self.indentationLevel + 1))

    def createStringInterpolatedValue(self, value):
        return "\\(%s)" % value
        
    def createParamName(self, name, type, userDefined):
        if (userDefined == True):        
            return "%s: %s" % (name, type)
        return "_ %s: %s" % (name, type)

    def createMethodDefinition(self, name, value):
        methodProps = super().createMethodDefinition(name, value)
        return [
            "static func %s(%s) -> String {" % (methodProps[0], methodProps[1]),
            "return \"%s\"" % (methodProps[2]),
            "}"
        ]

    def createEventClassDefinition(self):
        return [
            "struct EventData {"
            "\tlet name: String",
            "\tlet params: [String: Any]",
            "}"
        ]
    
    def createEventClassInstance(self, name, value):
        return "EventData(name: %s, params: %s)" % (name, value)

    def createMapDefinition(self, values):
        mapValues = super().createMapDefinition(values)
        return "mapOf(%s)" % (mapValues.replace("=",":"))

## 
## FILE GENERATION METHODS:
##
def generateStringFromCodeClass(codeClass):
    fileLines = [
        "// %s file generated by pykotlinswift script.\n\n" % codeClass.language        
    ]

    fileLines += codeClass.createEventClassDefinition()

    fileLines.append("\n\n")
    
    lines = codeClass.generateClassDefinitionLines()
    for line in lines:
        fileLines.append(line)

    classFile = ""    
    for line in fileLines:
        classFile += ("%s\n" % line)

    return classFile
    
def convertToSwiftFile(templateFileJson, className):    
    templateFileObject = json.loads(templateFileJson)
    
    if (isinstance(templateFileObject, object)):
        swiftClass = SwiftClass()
        swiftClass.name = className
        swiftClass.parseClassObject(templateFileObject)
        return generateStringFromCodeClass(swiftClass)

    return "invalid json"


def convertToKotlinFile(templateFileJson, className):    
    templateFileObject = json.loads(templateFileJson)
    
    if (isinstance(templateFileObject, object)):
        kotlinClass = KotlinClass()
        kotlinClass.name = className
        kotlinClass.parseClassObject(templateFileObject)
        return generateStringFromCodeClass(kotlinClass)

    return "invalid json"


if __name__ == '__main__':
    jsonFilePath = "test_template.json"
    eventsJsonFile = open(jsonFilePath)
    eventsJson = eventsJsonFile.read()
    eventsJsonFile.close()
    print(convertToSwiftFile(eventsJson, "TemplateTest"))