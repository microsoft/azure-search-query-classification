FROM python:3.9.10-slim-buster
COPY ./code/ /usr/local/src/myscripts
WORKDIR /usr/local/src/myscripts
RUN apt update
RUN apt install curl -y
RUN pip install -r requirements.txt
RUN python download_models.py
EXPOSE 80
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]
