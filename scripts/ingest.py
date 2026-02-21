import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from prometheus_client.parser import text_string_to_metric_families
from datetime import datetime
import logging
from sentence_transformers import SentenceTransformer


model = SentenceTransformer('all-MiniLM-L6-v2')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do Qdrant
qdrant_url = "http://192.168.0.43:6333"
client = QdrantClient(url=qdrant_url)
collection_name = "homelab_metrics"

# Garante que a coleção existe
client.recreate_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

nodes = {
    "notebook-verde-1": "http://192.168.0.43:9100/metrics",
    "notebook-verde-2": "http://192.168.0.48:9100/metrics",
    "notebook-i3": "http://192.168.0.46:9100/metrics"
}

def get_metrics_with_sdk(url):
    try:
        r = requests.get(url, timeout=3)
        # O SDK transforma o texto bruto em famílias de métricas
        metrics_families = text_string_to_metric_families(r.text)
        
        data = {}
        for family in metrics_families:
            for sample in family.samples:
                # CPU Load
                if sample.name == 'node_load1':
                    data['load'] = sample.value
                
                # Memória
                if sample.name == 'node_memory_MemAvailable_bytes':
                    data['mem_avail'] = sample.value
                if sample.name == 'node_memory_MemTotal_bytes':
                    data['mem_total'] = sample.value
                
                # Disco (filtrando pela label mountpoint usando o SDK)
                if sample.name == 'node_filesystem_size_bytes' and sample.labels.get('mountpoint') == '/':
                    data['disk_total'] = sample.value
                if sample.name == 'node_filesystem_free_bytes' and sample.labels.get('mountpoint') == '/':
                    data['disk_free'] = sample.value
        
        return data
    except Exception as e:
        logger.error(f"Erro ao coletar de {url}: {e}")
        return None

def main():
    for idx, (name, url) in enumerate(nodes.items()):
        m = get_metrics_with_sdk(url)
        
        if m and all(k in m for k in ['load', 'mem_avail', 'mem_total', 'disk_total', 'disk_free']):
            # Cálculos de porcentagem
            ram_pct = 100 - (m['mem_avail'] / m['mem_total'] * 100)
            disk_pct = 100 - (m['disk_free'] / m['disk_total'] * 100)
            
            # Texto para o banco de vetor
            status_text = (
                f"Status da máquina {name}: "
                f"Carga de CPU em {m['load']}, "
                f"RAM utilizada {ram_pct:.1f}%, "
                f"Disco RootFS ocupado {disk_pct:.1f}%."
            )

            # Vetor dummy (substitua por model.encode(status_text) para busca real)
            status_vector = model.encode(status_text).tolist()
            print(status_vector)

            client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=idx,
                        vector=status_vector,
                        payload={
                            "machine": name,
                            "text": status_text,
                            "timestamp": datetime.now().isoformat(),
                            "critical": disk_pct > 90 # Flag útil para busca rápida
                        }
                    )
                ]
            )
            logger.info(f"✅ {name} processado: {status_text}")

if __name__ == "__main__":
    main()