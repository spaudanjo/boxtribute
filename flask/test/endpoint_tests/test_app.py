import os

import pytest


@pytest.mark.skipif("CIRCLECI" not in os.environ, reason="only functional in CircleCI")
def test_get_box_details(mysql_app_client):
    data = {
        "query": """query BoxIdAndItems {
                qrCode(qrCode: "ffdd7f7243d74a663b417562df0ebeb") {
                    box {
                        id
                        boxLabelIdentifier
                        location {
                            id
                            base {
                                id
                            }
                            name
                        }
                        items
                        size
                        state
                    }
                }
            }"""
    }
    response = mysql_app_client.post("/graphql", json=data)
    queried_box = response.json["data"]["qrCode"]["box"]
    assert response.status_code == 200
    assert queried_box == {
        "id": "642",
        "boxLabelIdentifier": "436898",
        "items": 87,
        "location": {
            "id": "18",
            "base": {"id": "2"},
            "name": "WH2",
        },
        "size": "52 Mixed",
        "state": "InStock",
    }

    data = {
        "query": """query SomeBoxDetails {
                box(boxId: "996559") {
                    qrCode {
                        id
                        code
                        createdOn
                    }
                    product {
                        id
                    }
                    size
                    items
                }
            }"""
    }
    response = mysql_app_client.post("/graphql", json=data)
    queried_box = response.json["data"]["box"]
    assert response.status_code == 200
    assert queried_box == {
        "qrCode": {
            "id": "574",
            "code": "224ac643d3b929f99c71c25ccde7dde",
            "createdOn": None,
        },
        "items": 84,
        "product": {
            "id": "156",
        },
        "size": "53 S",
    }


@pytest.mark.skipif("CIRCLECI" not in os.environ, reason="only functional in CircleCI")
def test_get_boxes(mysql_app_client):
    data = {
        "query": """query CommentsOfLostBoxes {
                location(id: "1") {
                    boxes {
                        comment
                    }
                }
            }"""
    }
    response = mysql_app_client.post("/graphql", json=data)
    queried_boxes = response.json["data"]["location"]["boxes"]
    assert response.status_code == 200
    assert len(queried_boxes) == 27
    # There are no comments currently. Verify by creating a set
    assert {box["comment"] for box in queried_boxes} == {""}


@pytest.mark.skipif("CIRCLECI" not in os.environ, reason="only functional in CircleCI")
def test_get_bases(mysql_app_client):
    data = {
        "query": """query basesOfBoxAid {
                organisation(id: "1") {
                    bases {
                        name
                        organisation {
                            id
                        }
                    }
                }
            }"""
    }
    response = mysql_app_client.post("/graphql", json=data)
    queried_locations = response.json["data"]["organisation"]["bases"]
    assert response.status_code == 200
    assert len(queried_locations) == 1
    assert queried_locations[0]["name"] == "Lesvos"


@pytest.mark.skipif("CIRCLECI" not in os.environ, reason="only functional in CircleCI")
def test_get_products(mysql_app_client):
    data = {
        "query": """query getShoes {
                productCategory(id: "5") {
                    products {
                        id
                    }
                }
            }"""
    }
    response = mysql_app_client.post("/graphql", json=data)
    queried_products = response.json["data"]["productCategory"]["products"]
    assert response.status_code == 200
    assert len(queried_products) == 13


@pytest.mark.skipif("CIRCLECI" not in os.environ, reason="only functional in CircleCI")
def test_get_beneficiaries(mysql_app_client):
    data = {
        "query": """query getBeneficiariesOfLesvos {
                base(id: 1) {
                    beneficiaries {
                        id
                        tokens
                    }
                }
            }"""
    }
    response = mysql_app_client.post("/graphql", json=data)
    queried_beneficiaries = response.json["data"]["base"]["beneficiaries"]
    assert response.status_code == 200
    assert len(queried_beneficiaries) == 1006
    assert queried_beneficiaries[0]["tokens"] == 13


def test_user_permissions(client, mocker):
    """Verify that creating a beneficiary is not possible if user has
    insufficient permissions.
    """
    mocked_decode = mocker.patch("jose.jwt.decode")
    mocked_decode.return_value = {
        "https://www.boxtribute.com/email": "dev_volunteer@boxcare.org",
        "https://www.boxtribute.com/base_ids": ["2", "3"],
        "https://www.boxtribute.com/organisation_id": "2",
        "https://www.boxtribute.com/roles": ["Warehouse Volunteer"],
        "sub": "auth0|16",
        "permissions": ["qr:create", "stock:write"],
    }

    data = {
        "query": """mutation {
            createBeneficiary(
                beneficiaryCreationInput : {
                    firstName: "First",
                    lastName: "Last",
                    dateOfBirth: "1990-09-01",
                    baseId: 2,
                    groupIdentifier: "1312",
                    gender: Male,
                    languages: [de],
                    isVolunteer: true,
                    isRegistered: false
                }) {
                id
            }
            createBox(
                boxCreationInput : {
                    productId: 1,
                    items: 99,
                    locationId: 1,
                    comment: ""
                }) {
                id
            }
        }"""
    }
    response = client.post("/graphql", json=data)
    assert response.status_code == 200
    assert response.json["data"]["createBeneficiary"] is None
    assert len(response.json["errors"]) == 1
    assert response.json["errors"][0]["extensions"]["code"] == "FORBIDDEN"
