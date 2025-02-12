# utils/status_manager.py
import time
from threading import Thread, Event
from blinkstick import blinkstick
from typing import Optional

class StatusManager:
    def __init__(self):
        self.current_process = None
        self.stop_event = Event()
        self.blink_thread: Optional[Thread] = None
        # Initialize BlinkStick once
        self.bstick = blinkstick.find_first()
        if self.bstick is None:
            print("No BlinkStick found - status indicators will be disabled")

    def _blink_processing(self):
        if not self.bstick:
            return
            
        while not self.stop_event.is_set():
            self.bstick.set_color(red=0, green=0, blue=255)  # Blue
            time.sleep(0.5)
            self.bstick.turn_off()
            time.sleep(0.5)
    
    def start_process(self, process_name: str):
        """Start indicating a process is running"""
        self.current_process = process_name
        self.stop_event.clear()
        
        if self.blink_thread and self.blink_thread.is_alive():
            self.stop_event.set()
            self.blink_thread.join()
        
        self.blink_thread = Thread(target=self._blink_processing)
        self.blink_thread.start()
        
    def end_process(self, success: bool):
        """End current process with success/failure indication"""
        self.stop_event.set()
        if self.blink_thread:
            self.blink_thread.join()
        
        if self.bstick:
            if success:
                self.bstick.set_color(red=0, green=255, blue=0)  # Green
            else:
                self.bstick.set_color(red=255, green=0, blue=0)  # Red
            time.sleep(2)
            self.bstick.turn_off()
    
    def cleanup(self):
        """Clean up any running processes"""
        self.stop_event.set()
        if self.blink_thread:
            self.blink_thread.join()
        
        if self.bstick:
            self.bstick.turn_off()