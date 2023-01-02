import json
import os
import logging
import sys
import requests
from datetime import datetime, timedelta
import pandas as pd


class Requests:
    def __init__(self, baseEndpoint=None, headers=None):
        self.baseEndpoint = baseEndpoint
        self.headers = headers

    def getURI(self, endpoint=None):
        return requests.get(self.baseEndpoint + endpoint, headers=self.headers)

    def __del__(self):
        pass


class Logger:
    def __init__(self, logFileName='app.log', fileMode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
        logging.basicConfig(
            filename=logFileName,
            filemode=fileMode,
            format=format
        )

    def logDebug(self, message):
        logging.debug(message)

    def logInfo(self, message):
        logging.info(message)

    def logWarning(self, message):
        logging.warning(message)

    def logError(self, message):
        logging.error(message)

    def logCritical(self, message):
        logging.critical(message)

    def __del__(self):
        pass


class WazirXHelper:
    def __init__(self, creds, requestInstance, loggerInstance):
        self.creds = creds
        self.requestInstance = requestInstance
        self.loggerInstance = loggerInstance

    def checkSystemHealth(self):
        try:
            return self.requestInstance.getURI('/systemStatus')
        except Exception as e:
            self.loggerInstance.logError(str(e))
            sys.exit(1)

    def priceChangeStatistics24Hr(self, symbol=None):
        try:
            tickerPriceChangeEndpoint = '/tickers/24hr'
            if symbol:
                tickerPriceChangeEndpoint = '/ticker/24hr?symbol=' + symbol
            return self.requestInstance.getURI(tickerPriceChangeEndpoint)
        except Exception as e:
            self.loggerInstance.logError(str(e))
            sys.exit()

    def kLineData(self, symbol=None, limit=None, interval=None, startTime=None, endTime=None):
        try:
            if not symbol:
                raise Exception('symbol is required.')
            if not interval:
                raise Exception('interval is required.')
            kLineDataEndpoint = '/klines?symbol='+symbol+'&interval='+interval
            if startTime:
                kLineDataEndpoint += '&startTime='+str(int(startTime))
            if endTime:
                kLineDataEndpoint += '&endTime='+str(int(endTime))
            if limit:
                kLineDataEndpoint += '&limit='+str(limit)
            return self.requestInstance.getURI(kLineDataEndpoint)
        except Exception as e:
            self.loggerInstance.logError(str(e))
            sys.exit()

    def kLineDataBeforeXMin(self, symbol=None, limit=None, minutes=30):
        try:
            if not symbol:
                raise Exception('symbol is required.')
            interval = 1
            utcTimeNow = datetime.utcnow()
            utcTime30MinsBefore = utcTimeNow - \
                timedelta(minutes=minutes)
            epochTime = datetime(1970, 1, 1)
            totalSeconds30MinsBefore = (
                utcTime30MinsBefore - epochTime).total_seconds()
            return self.kLineData(symbol, limit, str(interval)+'m', totalSeconds30MinsBefore)

        except Exception as e:
            self.loggerInstance.logError(str(e))
            sys.exit()

    def __del__(self):
        pass


class CumulativeTrend(WazirXHelper):
    def executeStrategyWith30MinTimeFrame(self, symbol=None, quantity=None):
        try:
            if not symbol:
                raise Exception('symbol is required.')
            if not quantity:
                raise Exception('quantity is required.')

            # Getting data with t - 30 mins to t.
            kLineDataBefore30MinsJSONData = json.loads(
                self.kLineDataBeforeXMin(symbol, None, 30).content)
            kLineDataFrameBefore30Mins = pd.DataFrame(
                kLineDataBefore30MinsJSONData)

            # Getting Last 6 records
            kLineDataFrameBefore30Mins = kLineDataFrameBefore30Mins[:6]
            kLineDataFrameBefore30Mins.columns = [
                'Time', 'Open', 'High', 'Low', 'Close', 'Volume']
            kLineDataFrameBefore30Mins.set_index(
                'Time', inplace=True, drop=True)
            kLineDataFrameBefore30Mins = kLineDataFrameBefore30Mins.astype(
                float)
            return kLineDataFrameBefore30Mins

        except Exception as e:
            self.loggerInstance.logError(str(e))
            sys.exit()


def loadEnvironmentVariables(loggerInstance, jsonFileRelativePath):
    try:
        jsonContent = json.load(
            open(os.path.join(os.getcwd(), jsonFileRelativePath))
        )
        return jsonContent
    except Exception as e:
        loggerInstance.logError(str(e))
        sys.exit(1)


def main():
    loggerInstance = Logger()
    jsonEnvContent = loadEnvironmentVariables(loggerInstance, 'wazirx.json')
    requestInstance = Requests(jsonEnvContent['baseURI'], {
        'X-API-KEY': jsonEnvContent['ApiKey']
    })
    cumulativeTrendStrategy = CumulativeTrend(
        jsonEnvContent, requestInstance, loggerInstance)
    kLineDataFrameBefore30Mins = cumulativeTrendStrategy.executeStrategyWith30MinTimeFrame(
        'btcinr', 100)
    print(kLineDataFrameBefore30Mins)


if __name__ == '__main__':
    main()
