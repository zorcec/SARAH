import threading

CYCLE_TIME = 5 # 600 is 10 mins

room = data.get("room", None)
shouldHeat = data.get("heat", False)

logger.info("Requesting heating from: {}".format(room))

threading.Timer(CYCLE_TIME, heatingCycle).start()

def heatingCycle():
    if shouldHeat:
        heatingUpCycle()
    else:
        waitingCycle()

def heatingUpCycle():
    logger.info("Heating")

def waitingCycle():
    logger.info("Waiting")