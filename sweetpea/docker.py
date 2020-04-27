import docker
import os
import requests
import time

from datetime import datetime

def __external_docker_mgmt():
    return os.environ.get('SWEETPEA_EXTERNAL_DOCKER_MGMT') is not None


def update_docker_image(image_name):
    if __external_docker_mgmt():
        return

    print("Updating docker image '" + image_name + "'... ", end='', flush=True)
    try:
        t_start = datetime.now()
        docker.from_env().images.pull(image_name)
        t_end = datetime.now()
        print(str((t_end - t_start).seconds) + "s")
    except:
        print("An error occurred while updating the docker image, continuing with locally-cached image.")


def start_docker_container(image_name, portno):
    if __external_docker_mgmt():
        return
    port = portno
    if "SWEETPEA_DOCKER_PORT" in os.environ:
        port = int(os.environ["SWEETPEA_DOCKER_PORT"])
    print("Starting docker container from image '" + image_name + "' and exposing port " + str(port) + "... ", end='', flush=True)
    t_start = datetime.now()
    container = docker.from_env().containers.run(image_name, detach=True, ports={8080: port})
    t_end = datetime.now()
    print(str((t_end - t_start).seconds) + "s")
    time.sleep(1) # Give the server time to finish starting to avoid connection reset errors.

    check_server_health()

    return container


def check_server_health():
    port = 8080
    if "SWEETPEA_DOCKER_PORT" in os.environ:
        port = int(os.environ["SWEETPEA_DOCKER_PORT"])
    print("Checking server using port: " + str(port))
    health_check = requests.get('http://localhost:' + str(port) + '/')
    if health_check.status_code != 200:
        raise RuntimeError("SweetPea server healthcheck returned non-200 reponse! " + str(health_check.status_code))


def stop_docker_container(container):
    if __external_docker_mgmt():
        return

    print("Stopping docker container... ", end='', flush=True)
    t_start = datetime.now()
    container.stop(timeout = 0)
    container.remove()
    t_end = datetime.now()
    print(str((t_end - t_start).seconds) + "s")
