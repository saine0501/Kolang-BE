FROM python:3.10-slim
 
WORKDIR /code
 
COPY ./requirements.txt /code/requirements.txt

# 패키지 종속성 설치
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]