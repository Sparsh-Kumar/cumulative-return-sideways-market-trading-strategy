import logging


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
