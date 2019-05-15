import subprocess

from config.celery import app


@app.task
def create_docker_image(environment_id):
    from courses.models import Environment

    env = Environment.objects.get(pk=environment_id)

    process = subprocess.run(['docker', 'build', '-q', '-t', env.tag, '-'],
                             input=env.dockerfile_content, encoding='utf-8', capture_output=True)

    if process.returncode == 0:
        env.status = Environment.CREATED
    else:
        env.status = Environment.FAILED

    env.save()


@app.task
def delete_docker_image(tag):
    subprocess.run(['docker', 'rmi', tag], capture_output=True)


@app.task
def update_docker_image(tag, environment_id):
    delete_docker_image(tag)
    create_docker_image(environment_id)
