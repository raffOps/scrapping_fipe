FROM python:3.8
WORKDIR /HOME
RUN apt-get update
RUN apt-get install p7zip-full -y
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN apt-get install apt-transport-https ca-certificates gnupg -y
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
RUN apt-get update && apt-get install google-cloud-sdk -y

COPY requirements.txt requirements.txt
COPY entrypoint.sh entrypoint.sh
COPY key.json .
COPY extract.py .
COPY FIPE.py .

RUN pip install -r requirements.txt

RUN chmod +x entrypoint.sh
#ENTRYPOINT ["./git_sync.sh"]