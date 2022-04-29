from subprocess import Popen
import os
api_code_path = os.path.join(os.path.curdir, "docker-api", "code")
os.chdir(api_code_path)
commands = [f"uvicorn --env-file {os.path.join('..','..','.env')} --port 8000 api:app", f"python {os.path.join('..','..','check-api-load.py')}"]
procs = [ Popen(i, shell=True) for i in commands ]
for p in procs:
   p.wait()