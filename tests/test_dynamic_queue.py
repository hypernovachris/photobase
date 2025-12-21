import sys
import os
from PyQt6.QtWidgets import QApplication

# Add root dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.thumbnail_generator import ThumbnailGenerator

def test_dynamic_queue():
    app = QApplication(sys.argv)
    generator = ThumbnailGenerator()
    
    print(f"Initial max size: {generator.max_queue_size}")
    
    # Fill queue with dummy data
    for i in range(20):
        generator.queue.append((f"file{i}", f"thumb{i}"))
        generator.pending_requests.add(f"file{i}")
        
    print(f"Queue filled to: {len(generator.queue)}")
    
    # Shrink limit
    print("Setting limit to 10...")
    generator.setMaxQueueSize(10)
    
    print(f"New max size: {generator.max_queue_size}")
    print(f"Queue size after trim: {len(generator.queue)}")
    
    passed = True
    if generator.max_queue_size != 10:
        print("FAIL: Max size not updated")
        passed = False
        
    if len(generator.queue) != 10:
        print("FAIL: Queue not trimmed correctly")
        passed = False
        
    # Verify we dropped the OLDEST (start of list)
    # Original queue was [file0, file1, ... file19]
    # After trimming 10 from start, we should have [file10...file19]
    if generator.queue[0][0] != "file10":
        print(f"FAIL: Wrong items dropped. First item is {generator.queue[0][0]}")
        passed = False
        
    if passed:
        print("TEST PASSED: Dynamic queue sizing working.")
    else:
        print("TEST FAILED")

if __name__ == "__main__":
    test_dynamic_queue()
