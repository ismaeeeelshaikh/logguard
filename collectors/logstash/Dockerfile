FROM docker.elastic.co/logstash/logstash:8.11.0

RUN rm -f /usr/share/logstash/pipeline/logstash.conf

COPY logstash.conf /usr/share/logstash/pipeline/logstash.conf

EXPOSE 5044 5000
