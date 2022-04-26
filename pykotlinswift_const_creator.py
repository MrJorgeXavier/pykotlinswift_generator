#!/usr/bin/env python3

import json
import re
import unicodedata
from sys import exit
from traceback import print_exc

def raiseException(msg):
    print("Error: %s" % msg)
    print_exc()
    exit(3)

def camelCasedString(x: str):
    diactrictsRemoved = u"".join([c for c in unicodedata.normalize('NFKD', x) if not unicodedata.combining(c)])
    specialCharactersRemoved = re.sub(r'[^\w]|_', ' ', diactrictsRemoved)
    camelCase = ""
    for i in range(0, len(specialCharactersRemoved)):        
        char = specialCharactersRemoved[i]        
        if char == " ": continue
        elif char.isdigit() or char.isupper(): camelCase += char
        elif i == 0: camelCase += char.lower()
        elif specialCharactersRemoved[i - 1] == " ": camelCase += char.upper()
        else: camelCase += char.lower()
    return camelCase

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
        self.defaultParameters = {}
        self.innerEnums = []

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

    def createEnumClassDefinition(self, name, caseParams):
        return None

    def createMethodDefinition(self, name, value):
        paramCount = 1
        methodArguments = ""
        methodReturnValue = ""

        splitValues = re.split("(%[sfd][^\{])|(%[sfd]$)|(%[sfd]{[^}]+})", value)
        
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
                    paramType = "Double"
                elif ("s" in typeChar):
                    paramType = "String"
                elif ("%{" in splitValue):
                    paramType = splitValue[2:len(splitValue) - 1]

                # Define name of param
                paramHasName = "{" in splitValue
                paramName = ""
                if (paramHasName):
                    paramName = re.findall("\{(.*)\}", splitValue)[0]
                    paramName = camelCasedString(paramName)
                else:
                    paramName = "a%d" % paramCount                                

                paramCount += 1
                
                # Write arguments
                if (len(methodArguments) > 0):
                    methodArguments = "%s, " % (methodArguments)

                methodArguments = "%s%s" % (methodArguments, self.createParamName(paramName, paramType, paramHasName))

                # Write return value
                if ("%{" in splitValue):
                    paramName = "%s.pyRawValue" % paramName
                                        
                if (paramHasName):
                    methodReturnValue = "%s%s" % (methodReturnValue, self.createStringInterpolatedValue(paramName))
                else:
                    paramName = splitValue.replace(typeChar, "%s" % self.createStringInterpolatedValue(paramName))
                    methodReturnValue = "%s%s" % (methodReturnValue, paramName)
                
                continue
            
            methodReturnValue = "%s%s" % (methodReturnValue, splitValue)

        return (name, methodArguments, methodReturnValue)

    def createMapDefinition(self, values):
        params = ""
        for valueKey in values:
            value = values[valueKey]
            
            if (len(params) > 0):
                    params += ", "

            if (isinstance(value, str)):
                if ("%" in value):
                    if ("%{" in value):
                        params += "\"%s\" = %s.pyRawValue" % (valueKey, camelCasedString(valueKey))
                    else:
                        params += "\"%s\" = %s" % (valueKey, camelCasedString(valueKey))
                else:
                    params += "\"%s\" = \"%s\"" % (valueKey, value)
            elif (isinstance(value, float)):
                params += "\"%s\" = %.2f" % (valueKey, value)
            elif (isinstance(value, int)):
                params += "\"%s\" = %d" % (valueKey, value)            
            elif (isinstance(value, list)):
                raiseException("Arrays are not supported! Use only strings, floats, ints and objects.")
        return params


    def createEventMethodDefinition(self, methodName, eventName, eventParams, excludeParams):
        methodArguments = ""
        methodReturnValue = ""

        for paramName in self.defaultParameters:
            if (paramName in eventParams):
                continue
            eventParams[paramName] = self.defaultParameters[paramName]
        
        for paramName in excludeParams:
            if (paramName in eventParams):
                del eventParams[paramName]

        for paramName in eventParams:
            paramValue = eventParams[paramName]
            paramType = ""
            # Define type of param
            if (isinstance(paramValue, str)):
                if ("%" in paramValue):                
                    typeChar = re.findall("%.", paramValue)[0]
                
                    if ("d" in typeChar):
                        paramType = "Int"
                    elif ("f" in typeChar):
                        paramType = "Double"
                    elif ("s" in typeChar):
                        paramType = "String"
                    elif ("%{" in typeChar):
                        paramType = paramValue[2:(len(paramValue) - 1)]
                    else:
                        raiseException("Unknown param type for param %s at method %s" % (paramName, methodName))
                else:
                    continue # fixed value
            else:
                continue # fixed value

            # Write arguments
            if (len(methodArguments) > 0):
                methodArguments = "%s, " % (methodArguments)

            paramName = camelCasedString(paramName)

            methodArguments = "%s%s" % (methodArguments, self.createParamName(paramName, paramType, True))                                                

        # Write return value
        mapParams = self.createMapDefinition(eventParams)
        methodReturnValue = self.createEventClassInstance(eventName, mapParams)

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
                raiseException("Arrays are not supported! Use only strings, floats, ints and objects.")
            elif (isinstance(value, object)):
                if (key == "_defaultParams"):
                    self.defaultParameters = value
                elif (key == "_enums"):
                    for enumClass in value:
                        enum = self.createEnumClassDefinition(enumClass, value[enumClass])
                        self.innerEnums.append(enum)
                elif "_name" in value:
                    eventName = value["_name"]
                    eventParams = value["_params"]
                    excludeParams = []
                    if ("_excludeParams" in value):
                        excludeParams = value["_excludeParams"]

                    eventMethodLines = self.createEventMethodDefinition(key, eventName, eventParams, excludeParams)
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
        
        for enum in self.innerEnums:
            writeLine(enum, self.indentationLevel + 1)

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
    
    def createEventMethodDefinition(self, methodName, eventName, eventParams, excludeParams):
        methodProps = super().createEventMethodDefinition(methodName, eventName, eventParams, excludeParams)
        return [
            "fun %s(%s): EventData {" % (methodProps[0], methodProps[1]),
            "return %s" % (methodProps[2]),
            "}"
        ]

    def createEnumClassDefinition(self, name, caseParams):
        indent = self.indentation(self.indentationLevel + 1)
        enumHeader = """
%sinterface %s: PyRawRepresentable {
%s    companion object {
%s        private data class EnumData(override val pyRawValue: Any): %s
""" % (indent, name, indent, indent, name)
        enumCases = ""
        for case in caseParams:            
            value = caseParams[case]
            if (isinstance(value, str)):
                if ("%" in value):
                    if (value.count("%") > 1):
                        raiseException("Enums cannot have more than one parameter, but it has at case %s.%s with value %s" % (name, case, value))
                    methodProps = super().createMethodDefinition(case, value)
                    paramDefinition = methodProps[1]
                    argument = methodProps[2] 
                    argument = argument[2:len(argument) - 1] # trimming interpolation characters
                    enumCases += "\n%sfun %s(%s): %s = EnumData(%s)" % (indent + self.indentation(2), case, paramDefinition, name, argument)
                else:
                    enumCases += "\n%sval %s: %s = EnumData(\"%s\")" % (indent + self.indentation(2), case, name, value)    
            else:
                enumCases += "\n%sval %s: %s = EnumData(%s)" % (indent + self.indentation(2), case, name, value)
        enumFooter = """
%s    }
%s}        
""" % (indent, indent)
        return enumHeader + enumCases + enumFooter


    def createEventClassDefinition(self):
        return """
import java.text.Normalizer

private val pyDiactricsRegex = "\\\\p{Mn}+".toRegex()
private val pyNormalizationRegex = "[^\\\\w]".toRegex()

interface PyRawRepresentable {
    val pyRawValue: Any
}

fun String.pyNormalized(): String {
    return Normalizer.normalize(this.lowercase(), Normalizer.Form.NFD)
        .replace(pyDiactricsRegex, "")
        .replace(pyNormalizationRegex, "_")
        .split("_")
        .filter({  s -> s.length > 0 })
        .joinToString(separator = "_")
}

fun Map<String, Any>.pyNormalized(): Map<String, Any> {
    var map = HashMap<String, Any>()
    for ((key, value) in this) {
        if (value is String) {
            map.put(key.pyNormalized(), value.pyNormalized())
        }
        else {
            map.put(key.pyNormalized(), value)
        }
    }
    return map
}

data class EventData(private val rawName: String, private val rawParams: Map<String, Any>) {
    val name = this.rawName.pyNormalized()
    val params = this.rawParams.pyNormalized()
    
    override fun toString() = "EventData(name=${this.name}, params=${this.params})"
}
        """

    def createEventClassInstance(self, name, value):
        return "EventData(\"%s\", %s)" % (name, value)

    def createMapDefinition(self, values):
        mapValues = super().createMapDefinition(values)
        return "mapOf(%s)" % (mapValues.replace("=","to"))
                

class SwiftClass(CodeClass):    
    def __init__(self):
        super().__init__(
            indentationCharacter="    ",
            language= "Swift",
            constKeyword= "public static let"
        )
    
    def createInnerClass(self):
        return SwiftClass()

    def createClassDefinition(self):        
        return "public struct %s {\n%sprivate init() {}\n" % (self.name, self.indentation(self.indentationLevel + 1))

    def createStringInterpolatedValue(self, value):
        return "\\(%s)" % value
        
    def createParamName(self, name, type, userDefined):
        if (userDefined == True):        
            return "%s: %s" % (name, type)
        return "_ %s: %s" % (name, type)

    def createMethodDefinition(self, name, value):
        methodProps = super().createMethodDefinition(name, value)
        return [
            "public static func %s(%s) -> String {" % (methodProps[0], methodProps[1]),
            "return \"%s\"" % (methodProps[2]),
            "}"
        ]
    
    def createEventMethodDefinition(self, methodName, eventName, eventParams, excludeParams):
        methodProps = super().createEventMethodDefinition(methodName, eventName, eventParams, excludeParams)
        return [
            "public static func %s(%s) -> EventData {" % (methodProps[0], methodProps[1]),
            "return %s" % (methodProps[2]),
            "}"
        ]

    def createEnumClassDefinition(self, name, caseParams):
        indent = self.indentation(self.indentationLevel + 1)
        enumHeader = """
%spublic struct %s: PyRawRepresentable {
%s    let pyRawValue: Any
%s    private init(_ value: Any) { self.pyRawValue = value }
""" % (indent, name, indent, indent)
        enumCases = ""
        for case in caseParams:            
            value = caseParams[case]
            if (isinstance(value, str)):
                if ("%" in value):
                    if (value.count("%") > 1):
                        raiseException("Enums cannot have more than one parameter, but it has at case %s.%s with value %s" % (name, case, value))
                    methodProps = super().createMethodDefinition(case, value)
                    paramDefinition = methodProps[1]
                    argument = methodProps[2] 
                    argument = argument[2:len(argument) - 1] # trimming interpolation characters
                    enumCases += "\n%spublic static func %s(%s) -> %s { return %s(%s) }" % (indent + self.indentation(1), case, paramDefinition, name, name, argument)
                else:
                    enumCases += "\n%spublic static let %s = %s(\"%s\")" % (indent + self.indentation(1), case, name, value)    
            else:
                enumCases += "\n%spublic static let %s = %s(%s)" % (indent + self.indentation(1), case, name, value)
        enumFooter = """
%s}        
""" % (indent)
        return enumHeader + enumCases + enumFooter


    def createEventClassDefinition(self):
        return  """
import Foundation

protocol PyRawRepresentable {
    var pyRawValue: Any { get }
}

extension String {
    func pyNormalized() -> String {
        let simple = folding(options: [.diacriticInsensitive, .widthInsensitive, .caseInsensitive], locale: nil)
        let nonAlphaNumeric = CharacterSet.alphanumerics.inverted
        return simple.components(separatedBy: nonAlphaNumeric)
            .joined(separator: "_")
            .split(separator: "_")
            .filter({ $0.count > 0 })
            .joined(separator: "_")
    }
}

extension Dictionary where Key == String, Value == Any {
    func pyNormalized() -> [Key: Value] {
        return self.reduce([:], { result, keyValue in
            var r = result
            r[keyValue.key.pyNormalized()] = ((keyValue.value as? String)?.pyNormalized()) ?? keyValue.value
            return r
        })
    }
}

public struct EventData {
    public let name: String
    public let params: [String: Any]
    
    init(name: String, params: [String: Any]) {
        self.name = name.pyNormalized()
        self.params = params.pyNormalized()
    }
}
        """
    
    def createEventClassInstance(self, name, value):
        return "EventData(name: \"%s\", params: %s)" % (name, value)

    def createMapDefinition(self, values):
        mapValues = super().createMapDefinition(values)
        return "[%s]" % (mapValues.replace("=",":"))

## 
## FILE GENERATION METHODS:
##
def generateStringFromCodeClass(codeClass, version):
    if (version == None):
        version = "0.0.0"
        
    fileLines = [
        "// %s file generated by pykotlinswift script. Version: %s \n\n" % (codeClass.language, version)        
    ]

    fileLines.append(codeClass.createEventClassDefinition())
    
    lines = codeClass.generateClassDefinitionLines()
    for line in lines:
        fileLines.append(line)

    classFile = ""    
    for line in fileLines:
        classFile += ("%s\n" % line)

    return classFile
    
def convertToSwiftFile(templateFileJson, className, version=None):    
    templateFileObject = json.loads(templateFileJson)
    
    if (isinstance(templateFileObject, object)):
        swiftClass = SwiftClass()
        swiftClass.name = className
        swiftClass.parseClassObject(templateFileObject)
        return generateStringFromCodeClass(swiftClass, version)

    return "invalid json"


def convertToKotlinFile(templateFileJson, className, version=None):    
    templateFileObject = json.loads(templateFileJson)
    
    if (isinstance(templateFileObject, object)):
        kotlinClass = KotlinClass()
        kotlinClass.name = className
        kotlinClass.parseClassObject(templateFileObject)
        return generateStringFromCodeClass(kotlinClass, version)

    return "invalid json"


if __name__ == '__main__':
    jsonFilePath = "test_template.json"
    eventsJsonFile = open(jsonFilePath)
    eventsJson = eventsJsonFile.read()
    eventsJsonFile.close()
    print(convertToSwiftFile(eventsJson, "SampleClass"))
    print(convertToKotlinFile(eventsJson, "SampleClass"))