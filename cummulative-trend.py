import json
import os
import logging
import sys
import requests
from datetime import datetime, timedelta
import pandas as pd
import time

# This would store the net profit / loss amount.
totalAmount = 0


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
    def getDataWith30MinTimeFrame(self, symbol=None):
        try:
            if not symbol:
                raise Exception('symbol is required.')

            # Getting data with t - 30 mins to t.
            kLineDataBefore30MinsJSONData = json.loads(
                self.kLineDataBeforeXMin(symbol, None, 30).content)
            kLineDataFrameBefore30Mins = pd.DataFrame(
                kLineDataBefore30MinsJSONData)

            kLineDataFrameBefore30Mins.columns = [
                'Time', 'Open', 'High', 'Low', 'Close', 'Volume']

            # We can make Time as an index column using the line below.
            # kLineDataFrameBefore30Mins.set_index(
            #    'Time', inplace=True, drop=True)

            # Converting values to floating
            kLineDataFrameBefore30Mins = kLineDataFrameBefore30Mins.astype(
                float)
            return kLineDataFrameBefore30Mins

        except Exception as e:
            self.loggerInstance.logError(str(e))
            sys.exit()

    def executeCumulativeTrendStrategy(self, symbol=None, quantityToTrade=100, percentageFell=-0.002, percentageRise=0.0015, isEnteredTrade=False):
        try:
            '''
                Strategy Description 
                ---------------------
                # Getting the data for 30 min time frame.
                # Getting Last 6 records
                # Buy if asset fell more than {{percentageFell}}% within the last 30 mins.
                # Sell if asset arises by more than {{percentageRise}}% or falls further by 0.15%
            '''
            global totalAmount
            timeOfTrade = None
            if not symbol:
                raise Exception('Symbol is required.')
            if not quantityToTrade:
                raise Exception('quantity is required.')
            while True:
                # Sleep for 5 seconds because of API rate limiting.
                time.sleep(5)
                kLineDataFrame = self.getDataWith30MinTimeFrame(symbol)
                kLineDataFrame = kLineDataFrame[:6]
                cumulativeReturnOfDataFrame = (
                    kLineDataFrame.Close.pct_change() + 1
                ).cumprod() - 1
                print('[*] Trying to BUY, Cum Ret at {} = {}'.format(datetime.now().strftime(
                    "%H:%M:%S"), cumulativeReturnOfDataFrame.iloc[-1]))
                # TODO : We need to calculate volatility before taking into account the %age fell.
                if not isEnteredTrade:
                    if cumulativeReturnOfDataFrame.iloc[-1] <= percentageFell:
                        # TODO: Create a market BUY order
                        priceToBuy = kLineDataFrame.iloc[-1]['Close'] * \
                            quantityToTrade
                        totalAmount -= priceToBuy
                        print('Buy Quantity = {}, At = {}, Total Amount Left = {}'.format(
                            quantityToTrade, priceToBuy, totalAmount))
                        timeOfTrade = kLineDataFrame.iloc[-1]['Time']
                        isEnteredTrade = True
                        break
            if isEnteredTrade:
                while True:
                    # Sleep for 5 seconds because of API rate limiting
                    time.sleep(5)
                    kLineDataFrame = self.getDataWith30MinTimeFrame(symbol)
                    kLineDataFrameSinceBuy = kLineDataFrame[kLineDataFrame.Time > timeOfTrade]
                    if len(kLineDataFrameSinceBuy) > 1:
                        cumulativeReturnOfDataFrame = (
                            kLineDataFrameSinceBuy.Close.pct_change() + 1
                        ).cumprod() - 1
                        print('[*] Trying to SELL, Cum Ret at {} = {}'.format(datetime.now().strftime(
                            "%H:%M:%S"), cumulativeReturnOfDataFrame.iloc[-1]))
                        # TODO : We need to calculate volatility before taking into account the %age rise.
                        # or cumulativeReturnOfDataFrame.iloc[-1] <= percentageFell:
                        if cumulativeReturnOfDataFrame.iloc[-1] >= percentageRise:
                            # TODO : Create a market SELL order
                            priceToSell = kLineDataFrameSinceBuy.iloc[-1]['Close'] * \
                                quantityToTrade
                            totalAmount += priceToSell
                            print('Sell Quantity = {}, At = {}, Total Amount Left = {}'.format(
                                quantityToTrade, priceToSell, totalAmount))
                            break
        except Exception as e:
            self.loggerInstance.logError(str(e))
            sys.exit(1)


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
    cumulativeTrendStrategy.executeCumulativeTrendStrategy('shibinr')


if __name__ == '__main__':
    main()
