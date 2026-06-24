FROM apache/spark:4.1.1-java21-python3 AS spark_src

FROM apache/airflow:latest

USER root

COPY --from=spark_src /opt/spark /opt/spark
COPY --from=spark_src /opt/java/openjdk /opt/java/openjdk

ENV SPARK_HOME=/opt/spark
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=/opt/spark/bin:/opt/java/openjdk/bin:${PATH}

COPY airflow/requirements.txt /requirements.txt

USER airflow

RUN pip install --no-cache-dir -r /requirements.txt