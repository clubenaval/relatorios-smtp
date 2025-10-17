FROM python:3.12-slim

WORKDIR /app

# Instalar dependências (inclui werkzeug para hash de senhas)
RUN pip install --no-cache-dir mysql-connector-python flask schedule pytz ldap3 Werkzeug flask-mail itsdangerous

# Copiar código e template
COPY app.py .
COPY config.py .
COPY database.py .
COPY log_parser.py .
COPY scheduler.py .
COPY auth.py .
COPY templates/ templates/
COPY static/ static/

# Expor porta do Flask
EXPOSE 5000

# Comando para rodar a app
CMD ["python", "app.py"]