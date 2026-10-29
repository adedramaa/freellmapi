import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE=Path(__file__).resolve().parent/'trellis2_client.py'
spec=importlib.util.spec_from_file_location('trellis2_client',MODULE)
client=importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)

class TrellisAuthSafetyTests(unittest.TestCase):
    def test_no_token_no_inference(self):
        with patch.dict(os.environ, {'HF_TOKEN':''}):
            with self.assertRaisesRegex(RuntimeError, 'AUTH_REQUIRED'):
                client.require_token()

    def test_bad_token_without_hf_prefix(self):
        with patch.dict(os.environ, {'HF_TOKEN':'abc'}):
            with self.assertRaisesRegex(RuntimeError, 'AUTH_REQUIRED'):
                client.require_token()

    def test_hf_account_free_allowed(self):
        fake=types.SimpleNamespace(HfApi=lambda:types.SimpleNamespace(whoami=lambda token:{'name':'adedrama','isPro':False}))
        with patch.dict(sys.modules, {'huggingface_hub':fake}):
            result=client.verify_account('hf_test')
            self.assertEqual(result['status'],'AUTH_OK')
            self.assertEqual(result['gpu_calls'],0)

    def test_wrong_hf_account_blocked(self):
        fake=types.SimpleNamespace(HfApi=lambda:types.SimpleNamespace(whoami=lambda token:{'name':'randomperson','isPro':False}))
        with patch.dict(sys.modules, {'huggingface_hub':fake}):
            with self.assertRaisesRegex(RuntimeError, 'AUTH_MISMATCH'):
                client.verify_account('hf_test')

    def test_paid_plan_blocked(self):
        fake=types.SimpleNamespace(HfApi=lambda:types.SimpleNamespace(whoami=lambda token:{'name':'adedrama','isPro':True}))
        with patch.dict(sys.modules, {'huggingface_hub':fake}):
            with self.assertRaisesRegex(RuntimeError, 'PAID_ACCOUNT_BLOCKED'):
                client.verify_account('hf_test')

    def test_generate_entrypoint_never_calls_probe_without_token(self):
        with patch.dict(os.environ,{'HF_TOKEN':''}), patch.object(sys,'argv',['trellis2_client.py','--mode','generate','--accept-free-quota','--image','nonexistent.png']), patch.object(client,'probe',side_effect=AssertionError('network forbidden')):
            with self.assertRaises(SystemExit) as result:
                client.main()
            self.assertEqual(result.exception.code,2)

if __name__=='__main__':
    unittest.main()
