FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt && \
    pip install -e . && \
    python setup.py build_ext --inplace
CMD ["pytest", "-q"]
