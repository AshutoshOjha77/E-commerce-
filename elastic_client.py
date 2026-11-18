from elasticsearch import AsyncElasticsearch

es_client: AsyncElasticsearch | None = None

async def init_elasticsearch():
    global es_client
    es_client = AsyncElasticsearch(hosts=["http://127.0.0.1:9200"])
    if await es_client.ping():
        print("ElasticSearch is connected")
    else:
        raise Exception("Could not connect the ElasticSearch")



async def close_elasticsearch():
    if es_client:
        await es_client.close()

def get_elasticsearch() -> AsyncElasticsearch:
    if es_client is None:
        raise RuntimeError("ElasticSearch is not intialized")
    return es_client

async def add_products_index():
    es = get_elasticsearch()
    pro = "products"

    if await es.indices.exists(index=pro):
        print("You already have products")
        return

    mapping = {
        "mappings":{
            "properties":{
                "id":{"type":"integer"},
                "name":{"type":"text",
                        "field":{
                            "keyword":{"type":"keyword"}
                        }
                        },
                "price_rs":{"type":"float"},
                "stock":{"type":"integer"}
            }
        }
    }
    await es.indices.create(index=pro, body=mapping)
    print("Products index created")
    