from django.test import TestCase
from unittest.mock import patch, MagicMock
from .services.security import validate_command
from .services.multi_agent import RouterAgent
from .models import RemoteHost, ChatSession, AgentTask

class SecurityTests(TestCase):
    def test_validate_command_safe(self):
        is_valid, msg = validate_command("ls -la")
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_validate_command_dangerous(self):
        is_valid, msg = validate_command("rm -rf /")
        self.assertFalse(is_valid)
        self.assertIn("bloqueado", msg)

class MultiAgentTests(TestCase):
    @patch('google.generativeai.GenerativeModel')
    def test_router_agent_ssh(self, mock_model):
        # Configura o mock para retornar SSH
        mock_instance = mock_model.return_value
        mock_instance.generate_content.return_value.text = "SSH"
        
        router = RouterAgent()
        result = router.route("Crie um arquivo teste.txt")
        self.assertEqual(result, "SSH")

    @patch('google.generativeai.GenerativeModel')
    def test_router_agent_rag(self, mock_model):
        # Configura o mock para retornar RAG
        mock_instance = mock_model.return_value
        mock_instance.generate_content.return_value.text = "RAG"
        
        router = RouterAgent()
        result = router.route("Como está o uso de CPU?")
        self.assertEqual(result, "RAG")

class ModelsTests(TestCase):
    def test_remote_host_creation(self):
        host = RemoteHost.objects.create(
            name="Test Host",
            hostname="1.2.3.4",
            username="admin",
            password="password"
        )
        self.assertEqual(str(host), "Test Host (1.2.3.4)")

    def test_chat_session_creation(self):
        session = ChatSession.objects.create(title="Test Session")
        self.assertIn("Test Session", str(session))
