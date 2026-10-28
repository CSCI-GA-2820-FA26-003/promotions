FROM python:3.12-slim AS dependencies

WORKDIR /build
COPY Pipfile Pipfile.lock ./
RUN pip install --no-cache-dir pipenv==2026.10.3 \
    && pipenv verify \
    && pipenv sync --system \
    && pip uninstall -y pipenv virtualenv

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

RUN groupadd --gid 1001 promotions \
    && useradd --uid 1001 --gid promotions --create-home promotions
WORKDIR /app
COPY --from=dependencies /usr/local /usr/local
COPY --chown=promotions:promotions service ./service
COPY --chown=promotions:promotions wsgi.py ./

USER promotions
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
