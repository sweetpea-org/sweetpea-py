import docker
import os
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


def start_docker_container(image_name, port):
    if __external_docker_mgmt():
        return

    print("Starting docker container from image '" + image_name + "' and exposing port " + str(port) + "... ", end='', flush=True)
    t_start = datetime.now()
    container = docker.from_env().containers.run(image_name, detach=True, ports={port: port})
    t_end = datetime.now()
    print(str((t_end - t_start).seconds) + "s")
    time.sleep(1) # Give the server time to finish starting to avoid connection reset errors.
    return container


def stop_docker_container(container):
    if __external_docker_mgmt():
        return

    print("Stopping docker container... ", end='', flush=True)
    t_start = datetime.now()
    container.stop()
    container.remove()
    t_end = datetime.now()
    print(str((t_end - t_start).seconds) + "s")
