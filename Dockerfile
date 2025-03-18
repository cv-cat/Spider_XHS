FROM python:3.9

WORKDIR /app

COPY . .

RUN npm install
RUN pip install --no-cache-dir -r requirements.txt

# docker build -t spider_xhs .
# docker run -it spider_xhs bash