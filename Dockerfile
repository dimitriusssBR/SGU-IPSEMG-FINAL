FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependências de sistema (LibreOffice para o "soffice" do converte_em_pdf.py)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libreoffice \
        libreoffice-calc \
        libreoffice-writer \
        libreoffice-draw \
        fonts-dejavu-core \
        fonts-liberation \
        libjpeg62-turbo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código e arquivos da raiz
COPY . .

# Cloud Run injeta PORT (normalmente 8080), seu main.py já usa os.getenv("PORT", 8000)

CMD ["python", "-m", "main"]
