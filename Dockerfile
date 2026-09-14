FROM python:3.12-slim
WORKDIR /app
COPY . /app
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["sh", "-c", "python patch_logos.py && python patch_mahash.py && python patch_ui_fix.py && python app.py"]
