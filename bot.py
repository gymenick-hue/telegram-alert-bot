import os
import time

print("====================================")
print("СТАРТ BOT.PY")
print("Python працює!")
print("PORT =", os.environ.get("PORT"))
print("BOT_TOKEN є:", bool(os.environ.get("BOT_TOKEN")))
print("====================================", flush=True)

while True:
    print("BOT.PY працює...", flush=True)
    time.sleep(10)
