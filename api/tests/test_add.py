import json
from models import Result


def test_add_success(client, session):
    res = client.post('/add', data=dict(a=1, b=1))
    assert res.status_code == 200

    response_data = json.loads(res.get_data())
    assert 'task_id' in response_data
    assert 'task_url' in response_data

    task_url = response_data['task_url']
    assert task_url

    task_id = response_data['task_id']
    assert task_id

    task_status_response = client.get(task_url)
    assert task_status_response.status_code == 200

    result = session.query(Result).filter(Result.task_id == task_id).first()
    assert result


def test_add_fail_missing_params(client, session):
    res = client.post('/add', data=dict(a=1))
    assert res.status_code == 400, str(res.get_data())

    result = session.query(Result).all()
    assert not result

    res = client.post('/add', data=dict(b=1))
    assert res.status_code == 400, str(res.get_data())

    result = session.query(Result).all()
    assert not result
