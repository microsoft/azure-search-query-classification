from subprocess import Popen
import os

api_code_path = os.path.join(os.path.curdir, "docker-api", "code")
# abs_env_path = os.path.abspath(os.path.join(os.getcwd(), ".env"))
os.chdir(api_code_path)

commands = ["uvicorn --env-file ../../.env --port 8000 api:app", "python ../../check-api-load.py"]
procs = [ Popen(i) for i in commands ]
for p in procs:
   p.wait()