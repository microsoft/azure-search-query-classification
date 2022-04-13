from subprocess import Popen
import os
os.chdir(r'.\docker-api\code')
commands = ["uvicorn --env-file ../../.env --port 8000 api:app", "python ../../check-api-load.py"]
procs = [ Popen(i) for i in commands ]
for p in procs:
   p.wait()