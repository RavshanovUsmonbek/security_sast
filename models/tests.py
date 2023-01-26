#     Copyright 2021 getcarrier.io
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from json import dumps, loads
from queue import Empty
from typing import List, Union

from sqlalchemy import Column, Integer, String, ARRAY, JSON, DateTime, and_
from sqlalchemy.sql import func

from tools import rpc_tools, db, db_tools, constants, secrets_tools

# from ...shared.utils.rpc import RpcMixin
# from ...shared.db_manager import Base
# from ...shared.models.abstract_base import AbstractBaseMixin
# from ...shared.constants import CURRENT_RELEASE
# from ...projects.connectors.secrets import get_project_hidden_secrets, unsecret

from pylon.core.tools import log  # pylint: disable=E0611,E0401


class SecurityTestsSAST(db_tools.AbstractBaseMixin, db.Base, rpc_tools.RpcMixin):
    """ Security Tests: SAST """
    __tablename__ = "security_tests_sast"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    project_name = Column(String(64), nullable=False)
    test_uid = Column(String(64), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(String(256), nullable=True, unique=False)
    test_parameters = Column(ARRAY(JSON), nullable=True)
    integrations = Column(JSON, nullable=True)
    schedules = Column(ARRAY(Integer), nullable=True, default=[])
    results_test_id = Column(Integer)
    scan_location = Column(String(128), nullable=False)
    source = Column(JSON, nullable=False)


    def handle_change_schedules(self, schedules_data: List[dict]):
        new_schedules_ids = set(i['id'] for i in schedules_data if i['id'])
        ids_to_delete = set(self.schedules).difference(new_schedules_ids)
        self.schedules = []
        for s in schedules_data:
            log.warning('!!!adding schedule')
            log.warning(s)
            self.add_schedule(s, commit_immediately=False)
        try:
            self.rpc.timeout(2).scheduling_delete_schedules(ids_to_delete)
        except Empty:
            ...
        self.commit()


    @property
    def scanners(self) -> list:
        try:
            return list(self.integrations.get('scanners', {}).keys())
        except AttributeError:
            return []


    @staticmethod
    def get_api_filter(project_id: int, test_id: Union[int, str]):
        log.info(f'getting filter int? {isinstance(test_id, int)}  {test_id}')
        if isinstance(test_id, int):
            return and_(
                SecurityTestsSAST.project_id == project_id,
                SecurityTestsSAST.id == test_id
            )
        return and_(
            SecurityTestsSAST.project_id == project_id,
            SecurityTestsSAST.test_uid == test_id
        )



    # def configure_execution_json(self, output="cc", execution=False, thresholds={}):
    #     """ Create configuration for execution """
    #     #
    #     if output == "dusty":
    #         #
    #         global_sast_settings = dict()
    #         global_sast_settings["max_concurrent_scanners"] = 1
    #         if "toolreports" in self.sast_settings.get("reporters_checked", list()):
    #             global_sast_settings["save_intermediates_to"] = "/tmp/intermediates"
    #         #
    #         actions_config = dict()
    #         if self.sast_settings.get("sast_target_type") == "target_git":
    #             git_url = self.sast_settings.get("sast_target_repo")
    #             branch = "master"
    #             if "@" in git_url[5:]:
    #                 branch = git_url[5:].split("@")[1]
    #                 git_url = git_url.replace(f"@{branch}", "")

    #             actions_config["git_clone"] = {
    #                 "source": git_url,
    #                 "branch": branch,
    #                 "target": "/tmp/code"
    #             }
    #             if self.sast_settings.get("sast_target_repo_user") != "":
    #                 actions_config["git_clone"]["username"] = secrets_tools.unsecret(self.sast_settings.get("sast_target_repo_user"), project_id=self.project_id)
    #             if self.sast_settings.get("sast_target_repo_pass") != "":
    #                 actions_config["git_clone"]["password"] = secrets_tools.unsecret(self.sast_settings.get("sast_target_repo_pass"), project_id=self.project_id)
    #             if self.sast_settings.get("sast_target_repo_key") != "":
    #                 actions_config["git_clone"]["key_data"] = secrets_tools.unsecret(self.sast_settings.get("sast_target_repo_key"), project_id=self.project_id)
    #         if self.sast_settings.get("sast_target_type") == "target_galloper_artifact":
    #             actions_config["galloper_artifact"] = {
    #                 "bucket": self.sast_settings.get("sast_target_artifact_bucket"),
    #                 "object": self.sast_settings.get("sast_target_artifact"),
    #                 "target": "/tmp/code",
    #                 "delete": False
    #             }
    #         if self.sast_settings.get("sast_target_type") == "target_code_path":
    #             actions_config["galloper_artifact"] = {
    #                 "bucket": "sast",
    #                 "object": f"{self.test_uid}.zip",
    #                 "target": "/tmp/code",
    #                 "delete": True
    #             }
    #         #
    #         scanners_config = dict()
    #         scanners_config[self.sast_settings.get("language")] = {
    #             "code": "/tmp/code"
    #         }
    #         if "composition" in self.sast_settings.get("options_checked", list()):
    #             scanners_config["dependencycheck"] = {
    #                 "comp_path": "/tmp/code",
    #                 "comp_opts": "--enableExperimental"
    #             }
    #         if "secretscan" in self.sast_settings.get("options_checked", list()):
    #             scanners_config["gitleaks"] = {
    #                 "code": "/tmp/code"
    #             }
    #         #
    #         reporters_config = dict()
    #         reporters_config["galloper"] = {
    #             "url": unsecret("{{secret.galloper_url}}", project_id=self.project_id),
    #             "project_id": f"{self.project_id}",
    #             "token": unsecret("{{secret.auth_token}}", project_id=self.project_id),
    #         }
    #         if "toolreports" in self.sast_settings.get("reporters_checked", list()):
    #             reporters_config["galloper_tool_reports"] = {
    #                 "bucket": "sast",
    #                 "object": f"{self.test_uid}_tool_reports.zip",
    #                 "source": "/tmp/intermediates",
    #             }
    #         if "quality" in self.sast_settings.get("reporters_checked", list()):
    #             reporters_config["galloper_junit_report"] = {
    #                 "bucket": "sast",
    #                 "object": f"{self.test_uid}_junit_report.xml",
    #             }
    #             reporters_config["galloper_quality_gate_report"] = {
    #                 "bucket": "sast",
    #                 "object": f"{self.test_uid}_quality_gate_report.json",
    #             }
    #             reporters_config["junit"] = {
    #                 "file": "/tmp/{project_name}_{testing_type}_{build_id}_report.xml",
    #             }
    #         #
    #         if "jira" in self.sast_settings.get("reporters_checked", list()):
    #             project_secrets = secrets_tools.get_project_hidden_secrets(self.project_id)
    #             if "jira" in project_secrets:
    #                 jira_settings = loads(project_secrets["jira"])
    #                 reporters_config["jira"] = {
    #                     "url": jira_settings["jira_url"],
    #                     "username": jira_settings["jira_login"],
    #                     "password": jira_settings["jira_password"],
    #                     "project": jira_settings["jira_project"],
    #                     "fields": {
    #                         "Issue Type": jira_settings["issue_type"],
    #                     }
    #                 }
    #         #
    #         if "email" in self.sast_settings.get("reporters_checked", list()):
    #             project_secrets = secrets_tools.get_project_hidden_secrets(self.project_id)
    #             if "smtp" in project_secrets:
    #                 email_settings = loads(project_secrets["smtp"])
    #                 reporters_config["email"] = {
    #                     "server": email_settings["smtp_host"],
    #                     "port": email_settings["smtp_port"],
    #                     "login": email_settings["smtp_user"],
    #                     "password": email_settings["smtp_password"],
    #                     "mail_to": self.sast_settings.get("email_recipients", ""),
    #                 }
    #                 reporters_config["html"] = {
    #                     "file": "/tmp/{project_name}_{testing_type}_{build_id}_report.html",
    #                 }
    #         #
    #         if "ado" in self.sast_settings.get("reporters_checked", list()):
    #             project_secrets = get_project_hidden_secrets(self.project_id)
    #             if "ado" in project_secrets:
    #                 reporters_config["azure_devops"] = loads(project_secrets["ado"])
    #         #
    #         if "rp" in self.sast_settings.get("reporters_checked", list()):
    #             project_secrets = get_project_hidden_secrets(self.project_id)
    #             if "rp" in project_secrets:
    #                 rp = loads(project_secrets.get("rp"))
    #                 reporters_config["reportportal"] = {
    #                     "rp_host": rp["rp_host"],
    #                     "rp_token": rp["rp_token"],
    #                     "rp_project_name": rp["rp_project"],
    #                     "rp_launch_name": "sast"
    #                 }

    #         # Thresholds
    #         tholds = {}
    #         if thresholds and any(int(thresholds[key]) > -1 for key in thresholds.keys()):
    #             for key, value in thresholds.items():
    #                 if int(value) > -1:
    #                     tholds[key.capitalize()] = int(value)
    #         #
    #         dusty_config = {
    #             "config_version": 2,
    #             "suites": {
    #                 "sast": {
    #                     "settings": {
    #                         "project_name": self.sast_settings.get("project_name"),
    #                         "project_description": self.name,
    #                         "environment_name": "target",
    #                         "testing_type": "SAST",
    #                         "scan_type": "full",
    #                         "build_id": self.test_uid,
    #                         "sast": global_sast_settings
    #                     },
    #                     "actions": actions_config,
    #                     "scanners": {
    #                         "sast": scanners_config
    #                     },
    #                     "processing": {
    #                         "min_severity_filter": {
    #                             "severity": "Info"
    #                         },
    #                         "quality_gate": {
    #                             "thresholds": tholds
    #                         },
    #                         "false_positive": {
    #                             "galloper": unsecret("{{secret.galloper_url}}", project_id=self.project_id),
    #                             "project_id": f"{self.project_id}",
    #                             "token": unsecret("{{secret.auth_token}}", project_id=self.project_id)
    #                         },
    #                         "ignore_finding": {
    #                             "galloper": unsecret("{{secret.galloper_url}}", project_id=self.project_id),
    #                             "project_id": f"{self.project_id}",
    #                             "token": unsecret("{{secret.auth_token}}", project_id=self.project_id)
    #                         }
    #                     },
    #                     "reporters": reporters_config
    #                 }
    #             }
    #         }
    #         #
    #         return dusty_config
    #     #
    #     job_type = "sast"
    #     container = f"getcarrier/{job_type}:{CURRENT_RELEASE}"
    #     parameters = {
    #         "cmd": f"run -b galloper:{job_type}_{self.test_uid} -s {job_type}",
    #         "GALLOPER_URL": unsecret("{{secret.galloper_url}}", project_id=self.project_id),
    #         "GALLOPER_PROJECT_ID": f"{self.project_id}",
    #         "GALLOPER_AUTH_TOKEN": unsecret("{{secret.auth_token}}", project_id=self.project_id),
    #     }
    #     if self.sast_settings.get("sast_target_type") == "target_code_path":
    #         parameters["code_path"] = self.sast_settings.get("sast_target_code")
    #     project_queues = get_project_queues(project_id=self.project_id)
    #     if self.region in project_queues["public"]:
    #         cc_env_vars = {
    #             "RABBIT_HOST": unsecret("{{secret.rabbit_host}}", project_id=self.project_id),
    #             "RABBIT_USER": unsecret("{{secret.rabbit_user}}", project_id=self.project_id),
    #             "RABBIT_PASSWORD": unsecret("{{secret.rabbit_password}}", project_id=self.project_id),
    #             "RABBIT_VHOST": "carrier"
    #         }
    #     else:
    #         cc_env_vars = {
    #             "RABBIT_HOST": unsecret("{{secret.rabbit_host}}", project_id=self.project_id),
    #             "RABBIT_USER": unsecret("{{secret.rabbit_project_user}}", project_id=self.project_id),
    #             "RABBIT_PASSWORD": unsecret("{{secret.rabbit_project_password}}", project_id=self.project_id),
    #             "RABBIT_VHOST": unsecret("{{secret.rabbit_project_vhost}}", project_id=self.project_id)
    #         }
    #     concurrency = 1
    #     #
    #     if output == "docker":
    #         docker_run = f"docker run --rm -i -t"
    #         if self.sast_settings.get("sast_target_type") == "target_code_path":
    #             docker_run = f"docker run --rm -i -t -v \"{self.sast_settings.get('sast_target_code')}:/code\""
    #         return f"{docker_run} " \
    #                f"-e project_id={self.project_id} " \
    #                f"-e galloper_url={unsecret('{{secret.galloper_url}}', project_id=self.project_id)} " \
    #                f"-e token=\"{unsecret('{{secret.auth_token}}', project_id=self.project_id)}\" " \
    #                f"getcarrier/control_tower:{CURRENT_RELEASE} " \
    #                f"-tid {self.test_uid}"
    #     if output == "cc":
    #         execution_json = {
    #             "job_name": self.name,
    #             "job_type": job_type,
    #             "concurrency": concurrency,
    #             "container": container,
    #             "execution_params": dumps(parameters),
    #             "cc_env_vars": cc_env_vars,
    #             "channel": self.region
    #         }
    #         if "quality" in self.sast_settings.get("reporters_checked", list()):
    #             execution_json["quality_gate"] = "True"
    #         return execution_json
    #     #
    #     return ""









# class SecurityTestsDAST(db_tools.AbstractBaseMixin, db.Base, rpc_tools.RpcMixin):
#     __tablename__ = "security_tests_dast"
#     id = Column(Integer, primary_key=True)
#     project_id = Column(Integer, unique=False, nullable=False)
#     project_name = Column(String(64), nullable=False)
#     test_uid = Column(String(64), unique=True, nullable=False)

#     name = Column(String(128), nullable=False)
#     description = Column(String(256), nullable=True, unique=False)

#     urls_to_scan = Column(ARRAY(String(128)), nullable=False)
#     urls_exclusions = Column(ARRAY(String(128)), nullable=True)
#     scan_location = Column(String(128), nullable=False)

#     test_parameters = Column(ARRAY(JSON), nullable=True)
#     integrations = Column(JSON, nullable=True)
#     schedules = Column(ARRAY(Integer), nullable=True, default=[])
#     results_test_id = Column(Integer)

#     def add_schedule(self, schedule_data: dict, commit_immediately: bool = True):
#         schedule_data['test_id'] = self.id
#         schedule_data['project_id'] = self.project_id
#         try:
#             schedule_id = self.rpc.timeout(2).scheduling_security_create_schedule(data=schedule_data)
#             log.info(f'schedule_id {schedule_id}')
#             updated_schedules = set(self.schedules)
#             updated_schedules.add(schedule_id)
#             self.schedules = list(updated_schedules)
#             if commit_immediately:
#                 self.commit()
#             log.info(f'self.schedules {self.schedules}')
#         except Empty:
#             log.warning('No scheduling rpc found')

    # def handle_change_schedules(self, schedules_data: List[dict]):
    #     new_schedules_ids = set(i['id'] for i in schedules_data if i['id'])
    #     ids_to_delete = set(self.schedules).difference(new_schedules_ids)
    #     self.schedules = []
    #     for s in schedules_data:
    #         log.warning('!!!adding schedule')
    #         log.warning(s)
    #         self.add_schedule(s, commit_immediately=False)
    #     try:
    #         self.rpc.timeout(2).scheduling_delete_schedules(ids_to_delete)
    #     except Empty:
    #         ...
    #     self.commit()

    # @property
    # def scanners(self) -> list:
    #     try:
    #         return list(self.integrations.get('scanners', {}).keys())
    #     except AttributeError:
    #         return []

    # @staticmethod
    # def get_api_filter(project_id: int, test_id: Union[int, str]):
    #     log.info(f'getting filter int? {isinstance(test_id, int)}  {test_id}')
    #     if isinstance(test_id, int):
    #         return and_(
    #             SecurityTestsDAST.project_id == project_id,
    #             SecurityTestsDAST.id == test_id
    #         )
    #     return and_(
    #         SecurityTestsDAST.project_id == project_id,
    #         SecurityTestsDAST.test_uid == test_id
    #     )

    def configure_execution_json(
            self,
            output='cc',
            thresholds={}
    ):

        if output == "dusty":
            from flask import current_app
            global_dast_settings = dict()
            loki_settings = current_app.config["CONTEXT"].settings["loki"]
            global_dast_settings["max_concurrent_scanners"] = 1

            # if "toolreports" in self.reporting:
            #     global_dast_settings["save_intermediates_to"] = "/tmp/intermediates"

            # Thresholds
            tholds = {}
            if thresholds and any(int(thresholds[key]) > -1 for key in thresholds.keys()):

                for key, value in thresholds.items():
                    if int(value) > -1:
                        tholds[key.capitalize()] = int(value)

            #
            # Scanners
            #

            scanners_config = dict()
            for scanner_name in self.integrations.get('scanners', []):
                try:
                    config_name, config_data = \
                        self.rpc.call_function_with_timeout(
                            func=f'dusty_config_{scanner_name}',
                            timeout=2,
                            context=None,
                            test_params=self.__dict__,
                            scanner_params=self.integrations["scanners"][scanner_name],
                        )
                    scanners_config[config_name] = config_data
                except Empty:
                    log.warning(f'Cannot find scanner config rpc for {scanner_name}')

            # # scanners_data
            # for scanner_name in self.scanners_cards:
            #     scanners_config[scanner_name] = {}
            #     scanners_data = (
            #             current_app.config["CONTEXT"].rpc_manager.node.call(scanner_name)
            #             or
            #             {"target": "urls_to_scan"}
            #     )
            #     for setting in scanners_data:
            #         scanners_config[scanner_name][setting] = self.__dict__.get(
            #             scanners_data[setting],
            #             scanners_data[setting]
            #         )

            #
            # Processing
            #

            processing_config = dict()
            for processor_name in self.integrations.get("processing", []):
                try:
                    config_name, config_data = \
                        self.rpc.call_function_with_timeout(
                            func=f"dusty_config_{processor_name}",
                            timeout=2,
                            context=None,
                            test_params=self.__dict__,
                            scanner_params=self.integrations["processing"][processor_name],
                        )
                    processing_config[config_name] = config_data
                except Empty:
                    log.warning(f'Cannot find processor config rpc for {processor_name}')

            processing_config["quality_gate"] = {
                "thresholds": tholds
            }

            # "min_severity_filter": {
            #     "severity": "Info"
            # },
            # "quality_gate": {
            #     "thresholds": tholds
            # },
            # # "false_positive": {
            # #     "galloper": secrets_tools.unsecret(
            # #         "{{secret.galloper_url}}",
            # #         project_id=self.project_id
            # #     ),
            # #     "project_id": f"{self.project_id}",
            # #     "token": secrets_tools.unsecret(
            # #         "{{secret.auth_token}}",
            # #         project_id=self.project_id
            # #     )
            # # },
            # # "ignore_finding": {
            # #     "galloper": secrets_tools.unsecret(
            # #         "{{secret.galloper_url}}",
            # #         project_id=self.project_id
            # #     ),
            # #     "project_id": f"{self.project_id}",
            # #     "token": secrets_tools.unsecret(
            # #         "{{secret.auth_token}}",
            # #         project_id=self.project_id
            # #     )
            # # }

            #
            # Reporters
            #

            reporters_config = dict()
            for reporter_name in self.integrations.get('reporters', []):
                try:
                    config_name, config_data = \
                        self.rpc.call_function_with_timeout(
                            func=f'dusty_config_{reporter_name}',
                            timeout=2,
                            context=None,
                            test_params=self.__dict__,
                            scanner_params=self.integrations["reporters"][reporter_name],
                        )
                    reporters_config[config_name] = config_data
                except Empty:
                    log.warning(f'Cannot find reporter config rpc for {reporter_name}')

            reporters_config["centry_loki"] = {
                "url": loki_settings["url"],
                "labels": {
                    "project_id": str(self.project_id),
                    "task_key": str(self.id),
                    "result_test_id": str(self.results_test_id),
                },
            }
            reporters_config["centry_status"] = {
                "url": secrets_tools.unsecret(
                    "{{secret.galloper_url}}",
                    project_id=self.project_id
                ),
                "token": secrets_tools.unsecret(
                    "{{secret.auth_token}}",
                    project_id=self.project_id
                ),
                "project_id": str(self.project_id),
                "test_id": str(self.results_test_id),
            }


            reporters_config["centry"] = {
                "url": secrets_tools.unsecret(
                    "{{secret.galloper_url}}",
                    project_id=self.project_id
                ),
                "token": secrets_tools.unsecret(
                    "{{secret.auth_token}}",
                    project_id=self.project_id
                ),
                "project_id": str(self.project_id),
                "test_id": str(self.results_test_id),
            }
            # TODO: check valid reports names
            # for report_type in self.reporting:
            #     if report_type == "toolreports":
            #         reporters_config["galloper_tool_reports"] = {
            #             "bucket": "dast",
            #             "object": f"{self.test_uid}_tool_reports.zip",
            #             "source": "/tmp/intermediates",
            #         }
            #
            #     elif report_type == "quaity":
            #         reporters_config["galloper_junit_report"] = {
            #             "bucket": "dast",
            #             "object": f"{self.test_uid}_junit_report.xml",
            #         }
            #         reporters_config["galloper_quality_gate_report"] = {
            #             "bucket": "dast",
            #             "object": f"{self.test_uid}_quality_gate_report.json",
            #         }
            #         reporters_config["junit"] = {
            #             "file": "/tmp/{project_name}_{testing_type}_{build_id}_report.xml",
            #         }
            #
            #     elif report_type == "jira":
            #         project_secrets = get_project_hidden_secrets(self.project_id)
            #         if "jira" in project_secrets:
            #             jira_settings = loads(project_secrets["jira"])
            #             reporters_config["jira"] = {
            #                 "url": jira_settings["jira_url"],
            #                 "username": jira_settings["jira_login"],
            #                 "password": jira_settings["jira_password"],
            #                 "project": jira_settings["jira_project"],
            #                 "fields": {
            #                     "Issue Type": jira_settings["issue_type"],
            #                 }
            #             }
            #
            #     elif report_type == "email":
            #         project_secrets = get_project_hidden_secrets(self.project_id)
            #         if "smtp" in project_secrets:
            #             email_settings = loads(project_secrets["smtp"])
            #             reporters_config["email"] = {
            #                 "server": email_settings["smtp_host"],
            #                 "port": email_settings["smtp_port"],
            #                 "login": email_settings["smtp_user"],
            #                 "password": email_settings["smtp_password"],
            #                 "mail_to": self.dast_settings.get("email_recipients", ""),
            #             }
            #             reporters_config["html"] = {
            #                 "file": "/tmp/{project_name}_{testing_type}_{build_id}_report.html",
            #             }
            #
            #     elif report_type == "ado":
            #         project_secrets = get_project_hidden_secrets(self.project_id)
            #         if "ado" in project_secrets:
            #             reporters_config["azure_devops"] = loads(
            #                 project_secrets["ado"]
            #             )
            #
            #     elif report_type == "rp":
            #         project_secrets = get_project_hidden_secrets(self.project_id)
            #         if "rp" in project_secrets:
            #             rp = loads(project_secrets.get("rp"))
            #             reporters_config["reportportal"] = {
            #                 "rp_host": rp["rp_host"],
            #                 "rp_token": rp["rp_token"],
            #                 "rp_project_name": rp["rp_project"],
            #                 "rp_launch_name": "dast"
            #             }

            dusty_config = {
                "config_version": 2,
                "suites": {
                    "dast": {
                        "settings": {
                            "project_name": self.project_name,
                            "project_description": self.name,
                            "environment_name": "target",
                            "testing_type": "DAST",
                            "scan_type": "full",
                            "build_id": self.test_uid,
                            "dast": global_dast_settings
                        },
                        # "actions": {
                        #     "git_clone": {
                        #         "source": "https://github.com/carrier-io/galloper.git",
                        #         "target": "/tmp/code",
                        #         "branch": "master",
                        #     }
                        # },
                        "scanners": {
                            "dast": scanners_config,
                            # "dast": {"nmap": {
                            #     "target": "http://scanme.nmap.org/",
                            #     "include_ports": "22,80,443"
                            # }},
                            # "sast": {
                            #     "python": {
                            #         "code": "/tmp/code",
                            #     },
                            # },
                        },
                        "processing": processing_config,
                        "reporters": reporters_config
                    }
                }
            }
            #
            log.info("Resulting config: %s", dusty_config)
            #
            return dusty_config

        job_type = "dast"
        # job_type = "sast"

        # container = f"getcarrier/{job_type}:{CURRENT_RELEASE}"
        # container = f"getcarrier/sast:latest"
        container = f"getcarrier/dast:latest"
        parameters = {
            "cmd": f"run -b centry:{job_type}_{self.test_uid} -s {job_type}",
            "GALLOPER_URL": secrets_tools.unsecret(
                "{{secret.galloper_url}}",
                project_id=self.project_id
            ),
            "GALLOPER_PROJECT_ID": f"{self.project_id}",
            "GALLOPER_AUTH_TOKEN": secrets_tools.unsecret(
                "{{secret.auth_token}}",
                project_id=self.project_id
            ),
        }
        cc_env_vars = {
            "RABBIT_HOST": secrets_tools.unsecret(
                "{{secret.rabbit_host}}",
                project_id=self.project_id
            ),
            "RABBIT_USER": secrets_tools.unsecret(
                "{{secret.rabbit_user}}",
                project_id=self.project_id
            ),
            "RABBIT_PASSWORD": secrets_tools.unsecret(
                "{{secret.rabbit_password}}",
                project_id=self.project_id
            )
        }
        concurrency = 1

        if output == "docker":
            return f"docker run --rm -i -t " \
                   f"-e project_id={self.project_id} " \
                   f"-e galloper_url={secrets_tools.unsecret('{{secret.galloper_url}}', project_id=self.project_id)} " \
                   f"-e token=\"{secrets_tools.unsecret('{{secret.auth_token}}', project_id=self.project_id)}\" " \
                   f"getcarrier/control_tower:{constants.CURRENT_RELEASE} " \
                   f"-tid {self.test_uid}"
        if output == "cc":
            channel = self.scan_location
            if channel == "Carrier default config":
                channel = "default"
            #
            execution_json = {
                "job_name": self.name,
                "job_type": job_type,
                "concurrency": concurrency,
                "container": container,
                "execution_params": dumps(parameters),
                "cc_env_vars": cc_env_vars,
                # "channel": self.region
                "channel": channel,
            }
            # todo: scanner_cards no longer present
            # if "quality" in self.scanners_cards:
            #     execution_json["quality_gate"] = "True"
            #
            log.info("Resulting CC config: %s", execution_json)
            #
            return execution_json

        return ""