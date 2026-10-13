FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import solcx; solcx.install_solc('0.8.18')"


COPY . /app

EXPOSE 5002

CMD ["python", "main.py"]