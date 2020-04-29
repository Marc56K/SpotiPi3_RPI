import threading

class UpdateThread(threading.Thread):

    def __init__(self, name):
        threading.Thread.__init__(self, None, None, name)
        self.cv = threading.Condition()
        self._shutdown = False
        self._sleepDuration = 1.0

    def setSleepDuration(self, duration):
        with self.cv:
            self._sleepDuration = duration

    def run(self):
        with self.cv:
            try:
                self.startup()
            except Exception as e:
                print("ERROR: " + str(e))
            while True:
                self.cv.wait(self._sleepDuration)
                if self._shutdown:
                    try:
                        self.cleanup()
                    except Exception as e:
                        print("ERROR: " + str(e))
                    return
                else:
                    try:
                        self.update()
                    except Exception as e:
                        print("ERROR: " + str(e))

    def shutdownRequested(self):
        with self.cv:
            return self._shutdown

    def stop(self):
        with self.cv:
            self._shutdown = True
            self.cv.notify_all()
        self.join()

    def startup(self):
        pass

    def update(self):
        pass

    def cleanup(self):
        pass
