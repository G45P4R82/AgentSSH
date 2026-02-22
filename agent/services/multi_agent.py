import os
import re
import logging
import google.generativeai as genai
from typing import Generator, Dict, Any, Callable
from .gemini import AgentExecutor
from agent.tasks import get_embedding_model, get_qdrant_client, COLLECTION_NAME

logger = logging.getLogger(__name__)

class RouterAgent:
    def __init__(self, model_name: str = 'gemini-2.5-flash'):
        self.model_name = model_name
        self.api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=self.api_key)
        
    def route(self, prompt: str) -> str:
        """
        Routes the prompt to 'SSH' or 'RAG'.
        """
        system_instruction = """Você é um Router Agent. Sua única função é classificar a intenção do usuário.
        
        REGRAS:
        - Responda APENAS com 'SSH' ou 'RAG'.
        
        CLASSIFICAÇÃO:
        - 'RAG': Se o usuário estiver perguntando sobre o STATUS, SAÚDE, MÉTRICAS, DISCO, RAM ou CPU das máquinas que foram coletadas automaticamente. 
          Exemplos: "Qual a carga do node 1?", "Alguma máquina está com disco cheio?", "Como está a memória dos notebooks?".
        - 'SSH': Se o usuário estiver pedindo para EXECUTAR uma ação, listar arquivos, gerenciar processos, instalar algo ou qualquer tarefa interativa no terminal.
          Exemplos: "Reinicie o docker", "Me mostre os arquivos em /var/log", "Crie um arquivo teste.txt", "Qual o uptime do servidor?".
        
        Se houver dúvida, prefira 'SSH'.
        """
        model = genai.GenerativeModel(self.model_name, system_instruction=system_instruction)
        response = model.generate_content(prompt)
        result = response.text.strip().upper()
        
        if 'RAG' in result:
            return 'RAG'
        return 'SSH'

class RAGAgent:
    def __init__(self, model_name: str = 'gemini-2.5-flash'):
        self.model_name = model_name
        self.api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=self.api_key)

    def retrieve_context(self, query: str, limit: int = 5) -> str:
        try:
            model = get_embedding_model()
            qdrant = get_qdrant_client()
            
            vector = model.encode(query).tolist()
            
            search_result = qdrant.query_points(
                collection_name=COLLECTION_NAME,
                query=vector,
                limit=limit
            ).points
            
            context = "Abaixo estão as métricas mais recentes coletadas dos servidores (via NodeExporter):\n\n"
            for res in search_result:
                context += f"- [{res.payload.get('timestamp')}] {res.payload.get('text')}\n"
            
            return context
        except Exception as e:
            logger.error(f"Erro no RAG Retrieve: {e}")
            return "Não foi possível recuperar métricas do banco de dados vetorial."

    def run(self, prompt: str) -> Generator[Dict[str, Any], None, None]:
        yield {"type": "thought", "content": "Consultando banco de dados vetorial (Qdrant) para obter métricas de infraestrutura..."}
        
        context = self.retrieve_context(prompt)
        
        system_instruction = f"""Você é um Especialista em Observabilidade e Infraestrutura.
        Sua tarefa é responder perguntas do usuário baseando-se APENAS no contexto de métricas fornecido.
        Se a informação não estiver no contexto, diga que não tem dados atualizados sobre isso.
        
        CONTEXTO:
        {context}
        
        Responda em Português de forma clara e técnica.
        """
        
        model = genai.GenerativeModel(self.model_name, system_instruction=system_instruction)
        response = model.generate_content(prompt)
        
        yield {"type": "answer", "content": response.text.strip()}

class MultiAgentOrchestrator:
    def __init__(self, session_id: str = None):
        self.session_id = session_id
        self.router = RouterAgent()
        self.rag_agent = RAGAgent()
        self.ssh_agent = AgentExecutor(session_id=session_id) # Usando o executor existente
        
    def run(self, prompt: str, execute_callback: Callable[[str], str], host_name: str = None, host_ip: str = None) -> Generator[Dict[str, Any], None, None]:
        # 1. Routing
        yield {"type": "thought", "content": "Analisando a intenção da sua mensagem..."}
        route = self.router.route(prompt)
        
        if route == 'RAG':
            yield {"type": "thought", "content": "Direcionando para o Agente de Especialista em Métricas (RAG)."}
            yield from self.rag_agent.run(prompt)
        else:
            yield {"type": "thought", "content": f"Direcionando para o Agente de Execução SSH (Host: {host_name})."}
            yield from self.ssh_agent.run_loop(prompt, execute_callback, host_name=host_name, host_ip=host_ip)
