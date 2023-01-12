import sys
import time
import json
import pandas as pd
from datetime import datetime
from wazirxHelper import WazirXHelper


class CumulativeTrend(WazirXHelper):
    def getDataWith30MinTimeFrame(self, symbol=None):
        try:
            if not symbol:
                raise Exception('symbol is required.')
            kLineDataBefore30MinsJSONData = json.loads(
                self.kLineDataBeforeXMin(symbol, None, 30).content)
            kLineDataFrameBefore30Mins = pd.DataFrame(
                kLineDataBefore30MinsJSONData)
            kLineDataFrameBefore30Mins.columns = [
                'Time', 'Open', 'High', 'Low', 'Close', 'Volume']
            '''
              We can make Time as an index column using the line below.
              kLineDataFrameBefore30Mins.set_index('Time', inplace=True, drop=True)
              Converting values to floating
            '''
            kLineDataFrameBefore30Mins = kLineDataFrameBefore30Mins.astype(
                float)
            kLineDataFrameBefore30Mins['HumanReadableTime'] = pd.to_datetime(
                kLineDataFrameBefore30Mins['Time'], unit='s')
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
            timeOfTrade = None
            if not symbol:
                raise Exception('Symbol is required.')
            if not quantityToTrade:
                raise Exception('quantity is required.')
            while True:
                # Sleep for 5 seconds because of API rate limiting.
                time.sleep(5)
                kLineDataFrame = self.getDataWith30MinTimeFrame(symbol)
                kLineDataFrame = kLineDataFrame.tail(6)
                print(kLineDataFrame)
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
                        self.totalAmount -= priceToBuy
                        print('Buy Quantity = {}, At = {}, Total Amount Left = {}'.format(
                            quantityToTrade, kLineDataFrame.iloc[-1]['Close'], self.totalAmount))
                        timeOfTrade = kLineDataFrame.iloc[-1]['Time']
                        isEnteredTrade = True
                        break
            if isEnteredTrade:
                while True:
                    # Sleep for 5 seconds because of API rate limiting
                    time.sleep(5)
                    kLineDataFrame = self.getDataWith30MinTimeFrame(symbol)
                    kLineDataFrameSinceBuy = kLineDataFrame[kLineDataFrame.Time > timeOfTrade]
                    print(kLineDataFrameSinceBuy)
                    if len(kLineDataFrameSinceBuy) > 1:
                        cumulativeReturnOfDataFrame = (
                            kLineDataFrameSinceBuy.Close.pct_change() + 1
                        ).cumprod() - 1
                        print('[*] Trying to SELL, Cum Ret at {} = {}'.format(datetime.now().strftime(
                            "%H:%M:%S"), cumulativeReturnOfDataFrame.iloc[-1]))
                        # TODO : We need to calculate volatility before taking into account the %age rise.
                        # or cumulativeReturnOfDataFrame.iloc[-1] <= percentageFell:
                        if cumulativeReturnOfDataFrame.iloc[-1] > percentageRise:
                            # TODO : Create a market SELL order
                            priceToSell = kLineDataFrameSinceBuy.iloc[-1]['Close'] * \
                                quantityToTrade
                            self.totalAmount += priceToSell
                            print('Sell Quantity = {}, At = {}, Total Amount Left = {}'.format(
                                quantityToTrade, kLineDataFrameSinceBuy.iloc[-1]['Close'], self.totalAmount))
                            break
        except Exception as e:
            self.loggerInstance.logError(str(e))
            sys.exit(1)
