import cv2
import time
import numpy as np

def test_codec(fourcc_str):
    out = cv2.VideoWriter(f'test_{fourcc_str}.mp4', cv2.VideoWriter_fourcc(*fourcc_str), 30, (1920, 1080))
    frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    start = time.time()
    for _ in range(100):
        out.write(frame)
    out.release()
    end = time.time()
    print(f"{fourcc_str} took {end - start:.2f} seconds")

test_codec('mp4v')
test_codec('avc1')
