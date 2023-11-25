FROM python:3.10.0b1-buster

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip
RUN pip3 install --upgrade pip 

COPY ./ /slack_ai
WORKDIR /slack_ai
RUN python3 -m pip install -e ".[all]"

CMD ["uvicorn", "slack_ai.app:app", "--host", "0.0.0.0", "--port", "30207", "--reload"]
