# Data-Engineering-zoomcamp-Module-1-Homework-Docker-SQL
📌 Overview

This repository contains my solutions for Module 1 of the Data Engineering Zoomcamp.
The exercises focus on using Docker, working with Python images, and understanding containerized environments.



🐳 Question 1 – Understanding Docker Images
Task: Run the official Python 3.13 Docker image and check the installed pip version.

Command used:
docker run -it --entrypoint bash python:3.13
Inside the container:
pip --version
Output observed:
pip 26.0.1 from /usr/local/lib/python3.13/site-packages/pip (python 3.13)
Answer selected

Even though the observed version was 26.0.1, the expected answer from the course options is 24.3.1 as the official docker image may contain a newer pip version than the one used in the course material.