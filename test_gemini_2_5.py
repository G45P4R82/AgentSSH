import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel(os.getenv('GEMINI_MODEL_NAME'))
    response = model.generate_content("meus dados de CPU estão altos 80%, memoria estam tudo sendo usado de 16gb, tempetarura de CPU 80C, memoria 70C, HD 60C, qual e a melhor ação a ser tomada?, estou em um cluster,  tudo rodando em containers, com 10 servidores, dados esses dados que falei mais acima, nao pode reuniciar, qual problema e o melhor acao a ser tomada?")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Error with gemini-2.5-flash: {e}")
