from flask import Flask, request, jsonify
from celery.utils.log import get_task_logger
from celery import Celery
from dotenv import load_dotenv
import sys, time, os

load_dotenv()

MYSQL_ROOT_PASSWORD=os.environ.get("MYSQL_ROOT_PASSWORD")
MYSQL_DATABASE=os.environ.get("MYSQL_DATABASE")
MYSQL_USER=os.environ.get("MYSQL_USER")
MYSQL_PASSWORD=os.environ.get("MYSQL_PASSWORD")
MYSQL_HOST=os.environ.get("MYSQL_HOST")
RABBITMQ_DEFAULT_USER=os.environ.get("RABBITMQ_DEFAULT_USER")
RABBITMQ_DEFAULT_PASS=os.environ.get("RABBITMQ_DEFAULT_PASS")

os.chdir('/ai')

def make_celery(app):
    celery = Celery(
        'ai',
        broker=app.config['broker_url'],
        # backend='rpc://',
        backend=app.config['result_backend'],
        include=['ai.tasks']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


logger = get_task_logger(__name__)


app = Flask(__name__)

app.config.update(
    broker_url='amqp://'+RABBITMQ_DEFAULT_USER+':'+RABBITMQ_DEFAULT_PASS+'@rabbitmq:5672/',
    result_backend='db+mysql://'+ MYSQL_USER +':'+ MYSQL_PASSWORD +'@db/DoodleDoodle'
)

celery_app = make_celery(app)

@app.route('/api/v1/start_predict' ,methods=['POST'])
def call_method():
    value = request.get_json()
    draw_id = value['draw_id']
    ranword = value['ranword']

    task = celery_app.send_task('ai_predict', kwargs={
        'draw_id': draw_id, 'ranword': ranword})

    task_id = task.id
    rettaskid = {"task_id":task_id}

    return rettaskid

#작업상태
@app.route('/api/v1/task_status')
def get_status():

    #상태 조회 제한 시간
    start = time.time()

    status = {"STARTED" : 1, "PENDING" : 1, "FAILURE" : 0, "SUCCESS" : 0, "RETRY" : 1}
    response_data = request.get_json()
    task_ids = response_data["task-id"]
    res, temp_str = 1, ""
    while (res):
        temp_str = _is_complete(task_ids)
        res = status[str(temp_str)]
        time.sleep(1.0) 
        #time.sleep(35.0)
        end = time.time()
        if((end-start)>30):
            print('시간이 초과되었습니다!!')
            return { "status" : "FAILURE"}

    return { "status" : temp_str}

def _is_complete(task_ids):
    for task_id in task_ids:
        status = celery_app.AsyncResult(task_id, app=celery_app)
        if not (str(status.state) == "SUCCESS" or str(status.state) == "FAILURE"):
            return str(status.state)
        elif status == "FAILURE":
            break
    else:
        return 'SUCCESS'
    return 'FAILURE'

#작업결과
@app.route('/simple_task_result/<task_id>')
def task_result(task_id):
    ret = celery_app.AsyncResult(task_id).result
    return str(ret)

if __name__ == '__main__':
    app.run()
