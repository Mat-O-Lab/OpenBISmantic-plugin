from ch.systemsx.cisd.common.logging import LogCategory
from org.apache.log4j import Logger

operationLog = Logger.getLogger(str(LogCategory.OPERATION) + '.recursive-export-api')


def info(*text):
    for line in ' '.join(map(str, text)).split('\n'):
        operationLog.info(line)


def error(*text):
    for line in ' '.join(map(str, text)).split('\n'):
        operationLog.error(line)
