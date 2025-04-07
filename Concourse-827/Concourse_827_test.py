import unittest
import argparse
from unittest.mock import patch, MagicMock, call
import subprocess
from Concourse_827 import (
    arguments_parse, concourse_login, fetch_pipelines_names, enable_logger, fetch_pipeline_definitions,
      extract_pipelines, tag_under_version, main
)



class TestPipelineCheck(unittest.TestCase):
    def setUp(self) ->  None: # изпълнява се преди всеки тест и реално сетъпва нов magicMock преди всеки тест и така е чисто за всеки нов тест
        self.patcher = patch("Concourse_827.print")
        self.patcher.start()
    
    def tearDown(self) -> None: # почиства ресурсите и временните файлове. Изпълнява се след всеки тест
        self.patcher.stop()


    @patch("argparse.ArgumentParser")
    def test_arguments_parse(self, mock_argparser):
        """Тест за валидни аргументи"""
        mock_argparser.return_value.parse_args.return_value = argparse.Namespace(
            concourse_url="http://example.com",
            concourse_team="team1",
            concourse_user="admin",
            concourse_password="password",
            iacbox_version=700
        )

        args = arguments_parse()

        self.assertEqual(args["concourse_url"], "http://example.com")
        self.assertEqual(args["concourse_team"], "team1")
        self.assertEqual(args["concourse_user"], "admin")
        self.assertEqual(args["concourse_password"], "password")
        self.assertEqual(args["iacbox_version"], 700)  # Default value
        
        mock_argparser.assert_called_once_with(description="Collect user input for Concourse and Docker.")
        
        mock_argparser().add_argument.assert_has_calls([
            call("--concourse_url", required=True, help="Concourse URL"),
            call("--concourse_team", required=True, help="Concourse team name"),
            call("--concourse_user", required=True, help="Concourse username"),
            call("--concourse_password", required=True, help="Concourse password"),
            call("--iacbox_version", type=int, default=700, help="iacBox version (default: 700)")
        ])
        mock_argparser().parse_args.assert_called_once()

    @patch("subprocess.run")
    def test_concourse_login(self, mock_subprocess):
        concourse_login("https://example.com", "team1", "admin", "password")

        # po-dolu shte proverim dali e izvikana komanda s pravilni argumenti
        mock_subprocess.assert_called_once_with(
            ["fly", "login", "-t", "dev", "-c", "https://example.com", "-n", "team1", "-u", "admin", "-p", "password"],
            check=True
        )
    
    @patch("json.loads")
    @patch("subprocess.run")
    def test_fetch_pipeline_names(self, 
                                  mock_subprocess_run,
                                    mock_json_loads):
        mock_json_loads.return_value = [{"name": "test", "pipeline_config": "test-config"}]

        self.assertEqual(["test"], fetch_pipelines_names())
        mock_subprocess_run.assert_called_once_with(["fly", "-t", "dev", "ps", "--json"], check=True, capture_output=True, text=True)
        mock_json_loads.assert_called_once_with(mock_subprocess_run.return_value.stdout)
        
    @patch("json.loads")
    @patch("subprocess.run") #side_effect=subprocess.CalledProcessError(1, "get-pipeline-definition"))
    def test_fetch_pipeline_definitions(self, mock_subprocess_run, mock_json_loads):
        mock_logger = MagicMock()
        pipeline_names = ["pipeline1", "pipeline2"]
        mock_subprocess_run.side_effect = [subprocess.CompletedProcess([], 0, stdout="some-output", stderr=None), subprocess.CompletedProcess([], 1, stdout=None, stderr="some-error")]
        result = fetch_pipeline_definitions(pipeline_names, mock_logger)
        self.assertDictEqual(result, {"pipeline1": mock_json_loads.return_value})
        mock_subprocess_run.assert_has_calls([call(["fly", "-t", "dev", "gp", "-p", "pipeline1", "--json"],
            capture_output=True), call(["fly", "-t", "dev", "gp", "-p", "pipeline2", "--json"],
            capture_output=True)])
        mock_logger.error.assert_called_once_with("Failed to fetch pipeline 'pipeline2' configuration. Reason: some-error")
        mock_json_loads.assert_called_once_with("some-output")


    @patch("Concourse_827.tag_under_version")
    def test_extract_pipelines(self, mock_tag_under_version):
        mock_logger = MagicMock()
        mock_tag_under_version.side_effect = [False, True]
        pipeline_definitions = {
            "pipeline1": {
                "jobs": [
                    {
                        "name": "test-job",
                        "plan": [
                            {
                                "config": {
                                    "image_resource": {
                                        "type": "registry-image",
                                        "source": {
                                            "tag": "v999",
                                        }
                                    }
                                },
                            }
                        ]
                    }
                ]
            },
            "pipeline2": {
                "jobs": [
                    {
                        "name": "test-job-fail",
                        "plan": [
                            {
                                "config": {
                                    "image_resource": {
                                        "type": "registry-image",
                                        "source": {
                                            "tag": "v799",
                                        }
                                    }
                                },
                            }
                        ]
                    }
                ]
            },
        }

        extract_pipelines(pipeline_definitions, mock_logger, "800")

        mock_logger.error.assert_called_once_with("Job 'test-job-fail' in pipeline 'pipeline2' has a tag with version 'v799'!")
        mock_tag_under_version.assert_has_calls([call("v999", '800'), call("v799", '800')])
    
    def test_tag_under_version(self):
        self.assertTrue(tag_under_version("v650", 700))
        self.assertFalse(tag_under_version("v700", 700)) 
        self.assertFalse(tag_under_version("v750", 700))
        self.assertFalse(tag_under_version("v700.5", 700)) 
        self.assertFalse(tag_under_version("version700", 700)) 
        self.assertFalse(tag_under_version("vX", 700))  
        self.assertFalse(tag_under_version("", 700))   
        self.assertFalse(tag_under_version(" v700", 700))
        self.assertFalse(tag_under_version("v700 ", 700))
        self.assertFalse(tag_under_version("v700", 0))  # iacbox_version = 0

    @patch("Concourse_827.logging")
    @patch("Concourse_827.os")
    def test_enable_logger_file_does_not_exist(self,
                                               mock_os,
                                               mock_logging):
        # Arrange
        mock_logging.getLogger.return_value = "some-logger-object"
        mock_os.path.exists.return_value = False

        self.assertEqual(enable_logger("some-log-path"), "some-logger-object") #act
        
        mock_os.path.exists.assert_called_once_with("some-log-path")
        mock_os.remove.assert_not_called()
        
        mock_logging.basicConfig.assert_called_once_with(filename="some-log-path", level=mock_logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        mock_logging.getLogger.assert_called_once() #assert

        
    @patch("Concourse_827.logging")
    @patch("Concourse_827.os")
    def test_enable_logger_file_exist(self, 
                                      mock_os,
                                      mock_logging):
        #arrange
        mock_logging.getLogger.return_value = "some-logger-object"
        mock_os.path.exists.return_value = True 
        

        self.assertEqual(enable_logger("some-log-path"), "some-logger-object")
        mock_os.remove.assert_called_once_with("some-log-path")
        mock_logging.basicConfig.assert_called_once_with(filename="some-log-path", level=mock_logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        mock_logging.getLogger.assert_called_once() 

    @patch("Concourse_827.enable_logger")
    @patch("Concourse_827.arguments_parse")
    @patch("Concourse_827.concourse_login")
    @patch("Concourse_827.fetch_pipelines_names")
    @patch("Concourse_827.fetch_pipeline_definitions")
    @patch("Concourse_827.extract_pipelines")
    @patch("Concourse_827.logging")
    def test_main(self,
                          mock_logging,
                          mock_extract_pipelines,
                          mock_fetch_pipeline_definitions,
                          mock_pipelines_names,
                          mock_concourse_login,
                          mock_arguments_parse,
                          mock_enable_logger):
        
        mock_arguments_parse.return_value = {
            "concourse_url":"http://example.com",
            "concourse_team":"team1",
            "concourse_user":"admin",
            "concourse_password":"password",
            "iacbox_version":"700"
        }

        main()
        
        mock_enable_logger.assert_called_once_with(log_file_path='/tmp/invalid_iacbox_versions.log')
        mock_arguments_parse.assert_called_once()
        mock_concourse_login.assert_called_once_with("http://example.com", "team1", "admin", "password")
        mock_pipelines_names.assert_called_once()
        mock_fetch_pipeline_definitions.assert_called_once_with(pipeline_names=mock_pipelines_names(), logger=mock_enable_logger())
        mock_extract_pipelines.assert_called_once_with(iacbox_version="700", pipeline_definitions=mock_fetch_pipeline_definitions(), logger=mock_enable_logger())
        mock_logging.shutdown.assert_called_once()

    
if __name__ == "__main__":
    unittest.main()