# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install .

RUN pip install --no-cache-dir --upgrade pip uv
# COPY ./requirements.txt /code/requirements.txt
RUN uv pip install --system --no-cache-dir --upgrade -r requirements.txt
RUN uv pip install --system .


# Make port 8000 available to the world outside this container
EXPOSE 8000
EXPOSE 5005


CMD ["gunicorn", "--preload", "--timeout", "60", "--workers", "16", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "server:api"]
