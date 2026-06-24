FROM apache/spark:4.1.1-java21-python3
RUN mkdir -p /opt/spark/files/out/csv/_SUCCESS && chown -R spark:spark /opt/spark/files/out/csv/_SUCCESS
RUN wget -P /opt/spark/jars \
    -q https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.10/postgresql-42.7.10.jar
