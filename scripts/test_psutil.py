import psutil

cpu = psutil.cpu_percent(interval=1)
mem = psutil.virtual_memory()

print(f"CPU Usage: {cpu}%")
print(f"RAM available: {mem.available / (1024 ** 2):.0f} MB")
print(f"RAM used: {mem.percent}%")