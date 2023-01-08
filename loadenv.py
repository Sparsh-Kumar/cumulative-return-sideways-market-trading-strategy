import json
import os
import sys


def loadEnvironmentVariables(loggerInstance, jsonFileRelativePath):
    try:
        jsonContent = json.load(
            open(os.path.join(os.getcwd(), jsonFileRelativePath))
        )
        return jsonContent
    except Exception as e:
        loggerInstance.logError(str(e))
        sys.exit(1)
