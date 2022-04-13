FROM python:3.9.10-slim-buster
COPY ./code/ /usr/local/src/myscripts
WORKDIR /usr/local/src/myscripts
RUN pip install -r requirements.txt
EXPOSE 80
CMD ["streamlit", "run", "ui.py", "--server.port", "80"]