import hashlib
from flask_restful import Resource
from flask import request
from sqlalchemy import and_, or_, asc
from tools import api_tools

from ...models.reports import SecurityReport
from ...models.details import SecurityDetails
from ...models.results import SecurityResultsSAST
from pylon.core.tools import log  # pylint: disable=E0611,E0401


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        return {}, 200

    def post(self, project_id: int):
        file = request.files.get("file")
        if not file:
            return {"ok":False, "error": "Empty payload"}, 400

        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        api_tools.upload_file('tests', file, project, create_if_not_exists=True)
        meta = {
            'bucket': 'tests', 
            'filename': file.filename, 
            'project_id': project_id
        }
        return {"ok":True, "item":meta}, 201
    
    def delete(self, project_id: int):
        return {}, 204