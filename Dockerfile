FROM node:16 AS stylebuild

WORKDIR /home

COPY src/style/package.json .
COPY src/style/package-lock.json .
COPY src/style/webpack.config.js .
COPY src/style/src ./src

RUN npm install
RUN npm run build

FROM python:3.9.7

RUN apt update && apt install -y libvips

COPY --from=stylebuild /home/static /home/src/static

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY requirements_nonvidia.txt .
RUN pip install --no-cache-dir -r requirements_nonvidia.txt


COPY src /home/src

WORKDIR /home/src

CMD ["uvicorn", "--port", "50011", "--host", "0.0.0.0", "app:app"]