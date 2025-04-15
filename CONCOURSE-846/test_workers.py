import unittest 
from unittest.mock import patch, MagicMock, call
import config 
from workers import WorkersChecker 
from workers import InvalidWorkerCount

class TestWorkersChecker(unittest.TestCase):
    @patch('workers.WorkersChecker.bosh_login')
    @patch('workers.Context.load')
    @patch('workers.Credhub')
    def setUp(self, mock_credhub, mock_context_load, mock_bosh_login):
        self.ctx = mock_context_load
        self.credhub = mock_credhub
        self.bosh_login = mock_bosh_login
        self.checker = WorkersChecker()


    def test_constructor(self):
        self.assertEqual(self.checker.context, self.ctx.return_value)
        self.assertEqual(self.checker.credhub, self.credhub.return_value)
        self.assertEqual(self.checker.bosh_cli, self.bosh_login.return_value)
        self.ctx.assert_called_once()
        self.credhub.assert_called_once_with(ctx=self.ctx.return_value)
        self.bosh_login.assert_called_once()

    @patch("workers.bosh")
    def test_bosh_login_success(self, mock_bosh):
        self.checker.context.context.imports.bosh.scripts.provision_client = "some/script.sh"
        self.checker.context.context.imports.bosh.director.hostname_or_ip = "192.168.0.2"
        self.checker.context.context.imports.bosh.director.port = "12121"
        self.checker.credhub.cmds.getimportedcredential.return_value = "fake-ca"

        mock_bosh.provision_bosh_user.return_value = {
            "client_id": "bosh-user",
            "client_secret": "bosh-pass"
        }
        
        #act
        self.assertEqual(self.checker.bosh_login(), mock_bosh.BoshCli.return_value)

        #assert
        mock_bosh.provision_bosh_user.assert_called_once_with("some/script.sh", "workers_check_script")
        self.checker.credhub.cmds.getimportedcredential.assert_called_once_with(".context.imports.bosh.director.ca_cert")
        mock_bosh.BoshCli.assert_called_once_with(
            url="https://192.168.0.2:12121",
            ca_cert="fake-ca",
            client="bosh-user",
            client_secret="bosh-pass"
        )
    
   
    def test_fetch_vms_success(self):
        self.checker.bosh_cli._vms.return_value = {"Tables": [{"Rows": "some-value"}]}
        self.assertEqual(self.checker.fetch_vms(), "some-value")
        self.checker.bosh_cli._vms.assert_called_once_with(deployment_name="concourse", print_command=False)

    def test_count_bosh_vms_success(self):
        # Arrange
        bosh_workers_data = [
            {"instance": "worker-product-cf/1112223333444", "process_state": "running"},
            {"instance": "worker-product-cf/222333444555", "process_state": "running"},
            {"instance": "worker-product-cf/333444555666", "process_state": "stopped"},
            {"instance": "other-instance/444555666777", "process_state": "running"}
        ]
            
        # Act
        result = self.checker.count_bosh_vms(bosh_workers_data)
            
        # Assert
        self.assertEqual(result, 2)
    
    @patch('workers.print')
    @patch("workers.WorkersChecker.fetch_vms")
    @patch("workers.WorkersChecker.count_bosh_vms")
    def test_execute_success(self, mock_count_bosh_vms, mock_fetch_vms, mock_print):
        # Arrange
        self.checker.context.context.config.worker_product_cf.instances = 2
      
        mock_count_bosh_vms.return_value = 2

        # Act
        self.checker.execute()

        # Assert
        mock_fetch_vms.assert_called_once()
        mock_count_bosh_vms.assert_called_once_with(bosh_workers_data=mock_fetch_vms.return_value)
        mock_print.assert_has_calls([call("this is the workers count in the config: 2"), call("this is the workers count in running state: 2"), call("Success, the workers count match")])

    @patch('workers.print')
    @patch("workers.WorkersChecker.fetch_vms")
    @patch("workers.WorkersChecker.count_bosh_vms")
    def test_execute_failure(self, mock_count_bosh_vms, mock_fetch_vms, mock_print):
        self.checker.context.context.config.worker_product_cf.instances = 3
       
        mock_count_bosh_vms.return_value = 2

        with self.assertRaises(InvalidWorkerCount) as iwc:
            self.checker.execute()
        
        self.assertEqual(str(iwc.exception), "Fail - The workers count doesn't match")
        mock_fetch_vms.assert_called_once()
        mock_count_bosh_vms.assert_called_once_with(bosh_workers_data=mock_fetch_vms.return_value)
        mock_print.assert_has_calls([call("this is the workers count in the config: 3"), call("this is the workers count in running state: 2")])
      
    
if __name__ == "__main__":
    unittest.main()
