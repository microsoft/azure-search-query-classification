import os, requests, time, logging

# Get logging options:
logger = logging.getLogger(__name__)

def check_api_load():
   try:
      r = requests.get(f"http://localhost:{port}/ready")
   except Exception:
      logging.info("Waiting for server loading")
      time.sleep(2)
      return False
   return True

port = 8000
while True:
   if check_api_load():
      break

logging.info("Server ready to serve requests")
code_path = os.path.join("..","..","docker-web","code","ui.py")
os.system(f'streamlit run {code_path} local_run')