from app.db.postgres import SessionLocal
from app.models.documents import Document
from app.db.elasticsearch import es
import random
from faker import Faker
from sqlalchemy.orm import Session
from elasticsearch.helpers import bulk


fake = Faker()

TENANTS = [
    "netflix",
    "amazon",
    "google",
    "microsoft",
    "apple",
    "meta",
    "openai",
    "uber",
    "spotify",
    "airbnb",
]


def bulk_insert(batch_size=10000):

    db: Session = SessionLocal()

    try:
        total = 1000000

        for start in range(0, total, batch_size):

            current_batch_size = min(batch_size, total - start)

            docs = [
                Document(
                    tenant_id=random.choice(TENANTS),
                    title=fake.sentence(nb_words=6),
                    content=fake.paragraph(nb_sentences=15),
                    indexed=False
                )
                for _ in range(current_batch_size)
            ]

            db.bulk_save_objects(docs, return_defaults=True)
            db.commit()

            print(f"Inserted {start + current_batch_size:,}")

    finally:
        db.close()



def bulk_index(batch_size=10000):
    db: Session = SessionLocal()

    offset = 0
    indexed = 0

    while True:
        documents = (
            db.query(Document)
            .filter(Document.indexed == False)
            .order_by(Document.id)
            .offset(offset)
            .limit(batch_size)
            .all()
        )

        if not documents:
            break

        actions = [
            {
                "_index": "documents",
                "_id": document.id,
                "_source": {
                    "tenant_id": document.tenant_id,
                    "title": document.title,
                    "content": document.content,
                    "created_at": document.created_at.isoformat() if document.created_at else None,
                },
            }
            for document in documents
        ]

        bulk(es, actions)

        db.query(Document).filter(Document.id.in_([document.id for document in documents])).update({"indexed": True})
        db.commit()

        indexed += len(documents)
        offset += batch_size

        print(f"Indexed {indexed:,}")

    db.close()




if __name__ == "__main__":
    # bulk_insert()
    bulk_index()
