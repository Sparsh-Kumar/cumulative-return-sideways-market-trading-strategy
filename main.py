from logger import Logger
from loadenv import loadEnvironmentVariables
from request import Requests
from strategy import CumulativeTrend


def main():
    loggerInstance = Logger()
    jsonEnvContent = loadEnvironmentVariables(loggerInstance, 'wazirx.json')
    requestInstance = Requests(jsonEnvContent['baseURI'], {
        'X-API-KEY': jsonEnvContent['ApiKey']
    })
    cumulativeTrendStrategy = CumulativeTrend(
        jsonEnvContent, requestInstance, loggerInstance)
    # cumulativeTrendStrategy.executeCumulativeTrendStrategy('shibinr', 130378090)


if __name__ == '__main__':
    main()
