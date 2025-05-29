FROM openjdk:21-jdk-slim
WORKDIR /app
COPY target/BombPartyClient.jar BombPartyClient.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "BombPartyClient.jar"]
