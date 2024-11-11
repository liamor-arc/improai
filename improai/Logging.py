import logging

def initializeLogging(file_name):
    logging.basicConfig(filename=file_name,
        filemode='a',
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG)