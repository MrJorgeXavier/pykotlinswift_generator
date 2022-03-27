#!/usr/bin/env python3

from asyncore import write
import sys
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
    
    def createMethodDefinition(self, name, value):
        paramCount = 1
        methodArguments = ""
        methodReturnValue = ""

        splitValues = re.split("(%[sfd][^\{])|(%[sfd]{[^}]+})", value)
        
        for splitValue in splitValues:            
            if (splitValue == None or splitValue == ''): 
                continue
            
            if ("%" in splitValue):
                # Define type of param
                typeChar = re.findall("%.", splitValue)[0]
                
                paramType = ""
                if ("d" in typeChar):
                    paramType = "Int"
                elif ("f" in typeChar):
                    paramType = "%%Float"
                elif ("s" in typeChar):
                    paramType = "String"

                # Define name of param
                paramHasName = "{" in splitValue
                paramName = ""
                if (paramHasName):
                    paramName = re.findall("\{(.*)\}", splitValue)[0]
                else:
                    paramName = "a%d" % paramCount                
                
                paramCount += 1
                
                # Write arguments
                if (len(methodArguments) > 0):
                    methodArguments = "%s, " % (methodArguments)

                methodArguments = "%s%s: %s" % (methodArguments, paramName, paramType)

                # Write return value
                if (paramHasName):
                    methodReturnValue = "%s%s" % (methodReturnValue, self.createStringInterpolatedValue(paramName))
                else:
                    paramName = splitValue.replace("%s%s" % ("%", typeChar), "$%s" % (paramName))
                    methodReturnValue = "%s%s" % (methodReturnValue, self.createStringInterpolatedValue(paramName))
                
                continue
            
            methodReturnValue = "%s%s" % (methodReturnValue, splitValue)

        return (name, methodArguments, methodReturnValue)

    def parseClassObject(self, jsonObject):
        self.name = jsonObject["className"]
        properties = jsonObject["classProperties"]

        for key in properties:
            value = properties[key]
            if (isinstance(value, str)):
                if "%" in value:
                    self.methodProperties.append(self.createMethodDefinition(key, value))
                else:
                    self.attributeLines.append(("%s %s = \"%s\"" % (self.constKeyword, key, value)))
            elif (isinstance(value, float)):
                self.attributeLines.append(("%s %s = %.2f" % (self.constKeyword, key, value)))
            elif (isinstance(value, int)):
                self.attributeLines.append(("%s %s = %d" % (self.constKeyword, key, value)))
            elif (isinstance(value, object)):
                innerClass = self.createInnerClass()
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
            writeLine(method, self.indentationLevel + 1)

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

    def createMethodDefinition(self, name, value):
        methodProps = super().createMethodDefinition(name, value)
        return "fun %s(%s): String { return \"%s\" }" % (methodProps[0], methodProps[1], methodProps[2])
    

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
        
    def createMethodDefinition(self, name, value):
        methodProps = super().createMethodDefinition(name, value)
        return "static func %s(%s) -> String { return \"%s\" }" % (methodProps[0], methodProps[1], methodProps[2])


## 
## FILE GENERATION METHODS:
##
def generateStringFromCodeClass(codeClass):
    fileLines = ["// %s file generated by const_creator python script\n" % codeClass.language]
    
    lines = codeClass.generateClassDefinitionLines()
    for line in lines:
        fileLines.append(line)

    classFile = ""    
    for line in fileLines:
        classFile += ("%s\n" % line)

    return classFile
    
def convertToSwiftFile(templateFileJson):    
    templateFileObject = json.loads(templateFileJson)
    
    if (isinstance(templateFileObject, object)):
        swiftClass = SwiftClass()
        swiftClass.parseClassObject(templateFileObject)
        return generateStringFromCodeClass(swiftClass)

    return "invalid json"


def convertToKotlinFile(templateFileJson):    
    templateFileObject = json.loads(templateFileJson)
    
    if (isinstance(templateFileObject, object)):
        swiftClass = KotlinClass()
        swiftClass.parseClassObject(templateFileObject)
        return generateStringFromCodeClass(swiftClass)

    return "invalid json"

if __name__ == '__main__':    
    print(SwiftClass().createMethodDefinition("nomeDoMetodo", "tab_bar_click_%d{numberOfClicks}_times"))
    # args = sys.argv[1:]
    
    # templateFilePath = "_temp/template.json"
    
    # if (len(args) != 0):
    #     templateFilePath = args[0]

    # templateFileJson = open(templateFilePath).read()
    
    # swiftFile = convertToSwiftFile(templateFileJson)

    # print(swiftFile)

    # kotlinFile = convertToKotlinFile(templateFileJson)

    # print(kotlinFile)