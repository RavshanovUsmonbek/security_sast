from queue import Empty
from flask_restful import Resource
from pylon.core.tools import log
from flask import request
from sqlalchemy import and_
from ...models.tests import SecurityTestsSAST
from ...models.thresholds import SecurityThresholds
from ...utils import parse_test_data, run_test
from tools import api_tools


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        total, res = api_tools.get(project_id, request.args, SecurityTestsSAST)
        rows = []
        for i in res:
            test = i.to_json()
            schedules = test.pop('schedules', [])
            if schedules:
                try:
                    test['scheduling'] = self.module.context.rpc_manager.timeout(
                        2).scheduling_security_load_from_db_by_ids(schedules)
                except Empty:
                    ...
            test['scanners'] = i.scanners
            rows.append(test)
        return {"total": total, "rows": rows}, 200

    @staticmethod
    def get_schedules_ids(filter_) -> set:
        r = set()
        for i in SecurityTestsSAST.query.with_entities(SecurityTestsSAST.schedules).filter(
                filter_
        ).all():
            r.update(set(*i))
        return r

    def delete(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        try:
            delete_ids = list(map(int, request.args["id[]"].split(',')))
        except TypeError:
            return 'IDs must be integers', 400

        filter_ = and_(
            SecurityTestsSAST.project_id == project.id,
            SecurityTestsSAST.id.in_(delete_ids)
        )

        try:
            self.module.context.rpc_manager.timeout(3).scheduling_delete_schedules(
                self.get_schedules_ids(filter_)
            )
        except Empty:
            ...

        SecurityTestsSAST.query.filter(
            filter_
        ).delete()
        SecurityTestsSAST.commit()

        return {'ids': delete_ids}, 200

    def post(self, project_id: int):
        """
        Post method for creating and running test
        """

        run_test_ = request.json.pop('run_test', False)
        log.info('before test data')
        test_data, errors = parse_test_data(
            project_id=project_id,
            request_data=request.json,
            rpc=self.module.context.rpc_manager,
        )

        if errors:
            return errors, 400
            # return make_response(json.dumps(errors, default=lambda o: o.dict()), 400)

        log.warning('TEST DATA')
        log.warning(test_data)

        schedules = test_data.pop('scheduling', [])
        log.warning('schedules')
        log.warning(schedules)

        test = SecurityTestsSAST(**test_data)
        test.insert()

        test.handle_change_schedules(schedules)

        threshold = SecurityThresholds(
            project_id=test.project_id,
            test_name=test.name,
            test_uid=test.test_uid,
            critical=-1,
            high=-1,
            medium=-1,
            low=-1,
            info=-1,
            critical_life=-1,
            high_life=-1,
            medium_life=-1,
            low_life=-1,
            info_life=-1
        )
        threshold.insert()

        if run_test_:
            resp = run_test(test)
            return resp, resp.get('code', 200)
        return test.to_json()
