import time


class TimerModel:
    def __init__(self):
        self.elapsed_seconds = 0.0
        self.running = False
        self.last_start_monotonic = None

    def toggle(self):
        if self.running:
            if self.last_start_monotonic is not None:
                self.elapsed_seconds += time.monotonic() - self.last_start_monotonic
            self.running = False
            self.last_start_monotonic = None
        else:
            self.running = True
            self.last_start_monotonic = time.monotonic()

    def reset(self):
        self.elapsed_seconds = 0.0
        if self.running:
            self.last_start_monotonic = time.monotonic()

    def total_seconds(self):
        total = self.elapsed_seconds
        if self.running and self.last_start_monotonic is not None:
            total += time.monotonic() - self.last_start_monotonic
        return int(total)

    def formatted_time(self):
        total_seconds = self.total_seconds()
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"
