FROM node:16 as stylebuild

WORKDIR /home

COPY src/style/package.json .
COPY src/style/package-lock.json .
COPY src/style/webpack.config.js .
COPY src/style/src ./src

RUN npm install
RUN npm run build

FROM python:3.9.7 as transcrypt

RUN apt update && apt install -y openjdk-11-jre-headless
WORKDIR /home

COPY src/frontend/homepage.py .
COPY src/frontend/edit_item.py .
COPY src/frontend/item.py .
COPY src/frontend/shared.py .

RUN pip install Transcrypt==3.9.0 htmltree==0.7.6

RUN transcrypt -bm homepage.py && mv __target__ homepage
RUN transcrypt -bm edit_item.py && mv __target__ edit_item
RUN transcrypt -bm item.py && mv __target__ item


FROM python:3.9.7

RUN apt update && apt install -y libvips

COPY --from=stylebuild /home/static /home/src/static

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src /home/src

COPY --from=transcrypt /home/homepage /home/src/static/homepage
COPY --from=transcrypt /home/edit_item /home/src/static/edit_item
COPY --from=transcrypt /home/item /home/src/static/item


WORKDIR /home/src

CMD ["uvicorn", "--port", "50011", "--host", "0.0.0.0", "app:app"]