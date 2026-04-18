import time
from datetime import datetime

def log(direction, layer, src, dst, data):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

    print(f"""
[{ts}] [{direction}:{layer}]
  FROM : {src}
  TO   : {dst}
  DATA : {data}
""", flush=True)