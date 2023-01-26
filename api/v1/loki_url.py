import json
import gzip

import flask
from flask import make_response
from flask_restful import Resource
from pylon.core.tools import log
from pylon.core.seeds.minio import MinIOHelper


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):

        key = flask.request.args.get("task_id", None)
        result_key = flask.request.args.get("result_test_id", None)
        if not key or not result_key:  # or key not in state:
            return make_response({"message": ""}, 404)

        websocket_base_url = self.module.context.settings['loki']['url']
        websocket_base_url = websocket_base_url.replace("http://", "ws://")
        websocket_base_url = websocket_base_url.replace("api/v1/push", "api/v1/tail")

        # TODO: probably need to rename params
        # logs_query = "{" + f'task_key="{key}"' + "}"
        # logs_query = "{" + f'task_key="{key}"&result_test_id="{result_key}"&project_id="{project_id}"' + "}"
        logs_query = "{" + f'task_key="{key}",result_test_id="{result_key}",project_id="{project_id}"' + "}"

        # TODO: Uncomment or re-write when all settings will be ready
        # state = self._get_task_state()
        # logs_start = state[key].get("ts_start", 0)
        logs_start = 0
        logs_limit = 10000000000

        return make_response(
            {"websocket_url": f"{websocket_base_url}?query={logs_query}&start={logs_start}&limit={logs_limit}"},
            200
        )
