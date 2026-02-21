import logging
import requests

from celery import shared_task
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from prometheus_client.parser import text_string_to_metric_families
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Configurações — edite aqui ou mova para settings.py / .env
# ------------------------------------------------------------------
QDRANT_URL = "http://192.168.0.43:6333"
COLLECTION_NAME = "homelab_metrics"

NODES = {
    "notebook-verde-1": "http://192.168.0.43:9100/metrics",
    "notebook-verde-2": "http://192.168.0.48:9100/metrics",
    "notebook-i3":      "http://192.168.0.46:9100/metrics",
}

# O modelo é carregado uma única vez quando o worker sobe (cache do processo)
_embedding_model = None
_qdrant_client = None


def get_embedding_model():
    """Singleton: carrega o modelo apenas uma vez por processo worker."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Carregando SentenceTransformer all-MiniLM-L6-v2 …")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def get_qdrant_client():
    """Singleton: reutiliza a conexão com o Qdrant."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(url=QDRANT_URL)
    return _qdrant_client


def _ensure_collection(client: QdrantClient) -> None:
    """Cria ou recria a coleção se ela não existir."""
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        logger.info(f"Coleção '{COLLECTION_NAME}' criada no Qdrant.")


def _get_metrics(url: str) -> dict | None:
    """Coleta e parseia as métricas do Node Exporter."""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        families = text_string_to_metric_families(response.text)

        data = {}
        for family in families:
            for sample in family.samples:
                if sample.name == 'node_load1':
                    data['load'] = sample.value
                elif sample.name == 'node_memory_MemAvailable_bytes':
                    data['mem_avail'] = sample.value
                elif sample.name == 'node_memory_MemTotal_bytes':
                    data['mem_total'] = sample.value
                elif sample.name == 'node_filesystem_size_bytes' and sample.labels.get('mountpoint') == '/':
                    data['disk_total'] = sample.value
                elif sample.name == 'node_filesystem_free_bytes' and sample.labels.get('mountpoint') == '/':
                    data['disk_free'] = sample.value

        return data
    except Exception as exc:
        logger.error(f"Erro ao coletar métricas de {url}: {exc}")
        return None


# ------------------------------------------------------------------
# Task Celery
# ------------------------------------------------------------------
@shared_task(name='agent.tasks.ingest_homelab_metrics', bind=True, max_retries=3)
def ingest_homelab_metrics(self):
    """
    Coleta métricas de todos os nodes do homelab via Prometheus Node Exporter
    e armazena os embeddings no Qdrant.

    Agendada para rodar a cada 10 minutos via django-celery-beat.
    """
    logger.info("▶ Iniciando coleta de métricas do homelab …")

    model = get_embedding_model()
    qdrant = get_qdrant_client()
    _ensure_collection(qdrant)

    required_keys = {'load', 'mem_avail', 'mem_total', 'disk_total', 'disk_free'}
    processed = 0

    for idx, (name, url) in enumerate(NODES.items()):
        metrics = _get_metrics(url)

        if not metrics or not required_keys.issubset(metrics):
            logger.warning(f"⚠  {name}: dados incompletos ou nó indisponível.")
            continue

        ram_pct  = 100 - (metrics['mem_avail'] / metrics['mem_total'] * 100)
        disk_pct = 100 - (metrics['disk_free']  / metrics['disk_total'] * 100)

        status_text = (
            f"Status da máquina {name}: "
            f"Carga de CPU em {metrics['load']:.2f}, "
            f"RAM utilizada {ram_pct:.1f}%, "
            f"Disco RootFS ocupado {disk_pct:.1f}%."
        )

        vector = model.encode(status_text).tolist()

        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=idx,
                    vector=vector,
                    payload={
                        "machine":   name,
                        "text":      status_text,
                        "timestamp": datetime.utcnow().isoformat(),
                        "load":      metrics['load'],
                        "ram_pct":   round(ram_pct, 2),
                        "disk_pct":  round(disk_pct, 2),
                        "critical":  disk_pct > 90,
                    },
                )
            ],
        )

        logger.info(f"✅ {name}: {status_text}")
        processed += 1

    logger.info(f"◀ Coleta finalizada. {processed}/{len(NODES)} nodes processados.")
    return {"processed": processed, "total": len(NODES)}
