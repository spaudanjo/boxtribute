from boxwise_flask.db import db
from boxwise_flask.models.qr import Qr
from boxwise_flask.models.box import Box


def test_create_box(client):
    """Verify base GraphQL query endpoint"""
    mock_qr = {"id": 42, "code": "999"}

    db.connect_db()

    Qr.create(**mock_qr)

    db.close_db(None)

    gql_mutation_string = f"""mutation {{
    createBox(
        box_creation_input:{{
        product_id:1,
        items:9999,
        location_id:100000005,
        comments:"",
        size_id:1,
        qr_barcode:"999",
    }}){{
        id
        location_id
        product_id
        qr_id
    }}
    }}"""



    data = {"query": gql_mutation_string}
    response_data = client.post("/graphql", json=data)
    created_box = response_data.json["data"]

    assert response_data.status_code == 200

    assert created_box["location_id"] == 100000005
    assert created_box["product_id"] == 1
    assert created_box["qr_id"] == 42


