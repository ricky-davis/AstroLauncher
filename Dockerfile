FROM python:3.7-windowsservercore

WORKDIR C:/Build

COPY . .

RUN python -m pip install -r requirements.txt;

ENTRYPOINT ["python", "BuildEXE.py"]
