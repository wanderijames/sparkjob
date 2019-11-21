FROM wanderijames/spark:alpine

ENV SPARK_HOME=/opt/spark


# Install redshift deps and drivers
RUN echo "*** Installing redshift drivers ***" \
    && apk add \
        libpq \
        postgresql-dev \
    && wget https://s3.amazonaws.com/redshift-downloads/drivers/jdbc/1.2.36.1060/RedshiftJDBC42-no-awssdk-1.2.36.1060.jar \
    && mv RedshiftJDBC42-no-awssdk-1.2.36.1060.jar ${SPARK_HOME}/jars/RedshiftJDBC42-no-awssdk-1.2.36.1060.jar

ADD . /usr/local/lib/jobs
RUN ls /usr/local/lib/jobs \
    && pip install -e /usr/local/lib/jobs \
    && pip install tox
