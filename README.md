# Kotlin/Swift constants and events generator
------
I created this script solely for the specific purpose of generating the same constants to swift and kotlin from a json file. I found it useful to standardize my mobile applications analytics events. Probably no one will use this besides me, but I will keep public here anyways.<br>

## Features
- Generate enums, constants, optional params, and event methods to kotlin and swift from a json file
- Automatic normalization of values (lowercasing, removing diacritics, replacing special characters with underscore, removing repeated underscores) 
- Generation of methods with normalized camelCase param names (while keeping the event param name with the original value)

# How to use:

### 0: Clone this project and make it your working directory:
```
git clone git@github.com:MrJorgeXavier/pykotlinswift_generator.git
cd pykotlinswift_generator
```

### 1: Define a json file specifiying the constants and events:
```json
{    
    "_enums": { // Enum classes definitions that will be defined in the scope of this group
        "EnumClassName": { // The class name of the Enum
            "case1": "value1", // Defines a case with name "case1" and value "value1"
            "case2": "%s{paramName}" // Defines a case with name "case2" and the value as an string argument of name "paramName".
        }
    },
    "_defaultParams": { // Params that are added to all events in this group
        "defaultParam1": "%s", // Param with dynamic value will be added to all event methods signature
        "defaultParam2": 23  // Param with fixed value will be added to the EventData object construction, without alterations to the method signature
    },
    "eventMethodName": {  // Method that returns an EventData object
        "_name": "event-name", // The name property of the EventData object
        "_params": { // The params property of the EventData object
            "param1" : "%s", // Dynamic params are added to the method signature            
            "param2" : 42, // Fixed params are defined in the EventData construction
            "param3" : "%d{paramName}?", // Dynamic params values that ends with "?" are defined as optional params in the method signature.
        },
        "_excludeParams": ["defaultParam2"] // Optional. Exclude params inherited from the _defaultParams in this group.
    },
    "constantWithFixedStringValue": "value-one", // Defines a simple constant.
    "methodWithParam": "value-two-%s{stringParam}-and-%s-with-%d{intParam}", // Masks (%s, %d and %f) generates methods with arguments.
    "SubgroupOfPropertiesAndMethods": { // Creates a subgroup that can have events and constants.
        "constantWithFixedIntValue": 29,
        "constantWithFixedDoubleValue": 88.21
    }
}
```

### 2: Define an empty Kotlin file in your Android project:
```kotlin
/// Empty kotlin file to be the output target
```

### 3: Define an empty Swift file in your iOS Project:
```swift
/// Empty swift file to be the output target
```

### 4: Invoke the following script passing the paths to the created files, and the desired output class name as arguments to the script:
- Option 1: Pass all arguments in the script call:
```shell
python3 pykotlinswift.py json=<your-json-file-path> iosfile=<your-swift-file-path> androidfile=<your-kotlin-file-path> androidpackage=<your-kotlin-class-package> classname=<your-class-name> version=<file-version-to-append-on-file>
```
- Option 2: Define and pass a settings json file with the following keys in the script call:
```json
{
    "_version": "<file-version to append on file header commentary>",
    "_rootClassName": "<swift and kotlin class name to generate the main class that will contain all methods properties and subclasses>",    
    "_jsonTemplateFilePath": "<json constants and events definition as in the first step>",
    "_androidClassPackage": "<the package that will be specified at the top of the kotlin file (important to make the android project recognize the kotlin class)>",
    "_androidOutputFilePath": "<the path of the kotlin file inside the android project>",    
    "_iosOutputFilePath": "<the path of the swift file inside the ios project>"    
}
```
```shell
python3 pykotlinswift.py settings=<your-json-settings-file-path>
```

### After following the above steps, the example json will generate the following classes:
---
#### Swift file output:
```swift
// Swift file generated by pykotlinswift script.

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
    return self.reduce([:], {result, keyValue in
            var r = result
            r[keyValue.key] = nil
            r[keyValue.key.pyNormalized()] = ((keyValue.value as? String)?.pyNormalized()) ?? keyValue.value
            return r
        })
  }
}

public struct EventData {
    let name: String
    let params: [String: Any]

    init(name: String, params: [String: Any]) {
        self.name = name.pyNormalized()
        self.params = params.pyNormalized()
    }
}

public struct SampleClass {
    private init() {}

    public static let constantWithFixedStringValue = "value-one"

    public static func eventMethodName(param1: String, defaultParam1: String) -> EventData {
        return EventData(name: "event-name", params: ["param1" : param1, "param2" : 42, "defaultParam1" : defaultParam1])
    }
    public static func methodWithParam(stringParam: String, _ a2: String, intParam: Int) -> String {
        return "value-two-\(stringParam)-and-\(a2)-with-\(intParam)"
    }

    public struct SubgroupOfPropertiesAndMethods {
        private init() {}

        public static let constantWithFixedIntValue = 29
        public static let constantWithFixedDoubleValue = 88.21
    }
}
```

#### Kotlin file output:
```kotlin
// Kotlin file generated by pykotlinswift script.


import java.text.Normalizer

private val pyDiactricsRegex = "\\p{Mn}+".toRegex()
private val pyNormalizationRegex = "[^\\w]".toRegex()

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

object SampleClass {
    const val constantWithFixedStringValue = "value-one"

    fun eventMethodName(param1: String, defaultParam1: String): EventData {
        return EventData("event-name", mapOf("param1" to param1, "param2" to 42, "defaultParam1" to defaultParam1))
    }
    fun methodWithParam(stringParam: String, a2: String, intParam: Int): String {
        return "value-two-${stringParam}-and-${a2}-with-${intParam}"
    }

    object SubgroupOfPropertiesAndMethods {
        const val constantWithFixedIntValue = 29
        const val constantWithFixedDoubleValue = 88.21
    }
}
```

## Current Limitations:
- Arrays and booleans are not supported
- The output files must be created by the user, since they are indexed by the IDE.
- The special characters `{`, `}` and `%` are used to define dynamic params, and can not be used for any other purpose.
- The only dynamic mask values supported are `%f`, `%d` and `%s`.

### Future features:
- Visibility modifiers annotations
- Supporting arrays and booleans
- Adding custom formatting protocols
- Improvements in the script call to make it easier to use
- Code refactoring to be human readable
- Better definition of method signature to decouple it from param key/values
- Adding template project which has everything configured, including a html dashboad to control the events.
- Improving the events json structure to be more easily mantained
- README.md better written
- Support to code documentation
- Template project with everything working as intended
- Interpolated arguments on event params, just like on methods