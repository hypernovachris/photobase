import time
import face_recognition
import numpy as np
from PIL import Image

def benchmark():
    # Create a large image (e.g. 4000x3000)
    width, height = 4000, 3000
    print(f"Creating synthetic image {width}x{height}...")
    
    # Just random noise or a plain color with some features might differ in speed for CNN but for HOG it's mostly size.
    # We'll use a blank image to be consistent vs noise.
    # Actually, face_recognition converts to grayscale.
    img_data = np.zeros((height, width, 3), dtype=np.uint8) + 128
    
    print("Benchmarking full resolution scan...")
    start_time = time.time()
    # Face recognition expects array
    _ = face_recognition.face_locations(img_data)
    end_time = time.time()
    full_res_time = end_time - start_time
    print(f"Full resolution scan time: {full_res_time:.4f} seconds")
    
    # Resize to 1000px max dim
    target_dim = 1000
    scale = target_dim / max(width, height)
    new_w = int(width * scale)
    new_h = int(height * scale)
    
    print(f"Resizing to {new_w}x{new_h}...")
    # Use PIL for resizing to simulate actual workflow
    pil_img = Image.fromarray(img_data)
    pil_img = pil_img.resize((new_w, new_h))
    resized_data = np.array(pil_img)
    
    print("Benchmarking resized scan...")
    start_time = time.time()
    _ = face_recognition.face_locations(resized_data)
    end_time = time.time()
    resized_time = end_time - start_time
    print(f"Resized scan time: {resized_time:.4f} seconds")
    
    print(f"Speedup: {full_res_time / resized_time:.2f}x")

if __name__ == "__main__":
    benchmark()
