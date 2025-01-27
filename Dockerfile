FROM python:3.12-slim

RUN useradd --create-home --shell /bin/bash app_user

USER app_user

WORKDIR /home/app_user/gww-anomalies
COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install .

ENTRYPOINT ["python", "gww_anomalies/cli.py"]

CMD ["--help"]

