"""GraphQL query definitions"""
from ariadne import gql

query_defs = gql(
    """
    type Query {
        hello: String!
        allBases: [Base]
        orgBases(org_id: Int): [Base]
        base(id: Int!): Base
        allUsers: [User]
        user(email: String): User
        box(id: String): Box
        location(id: String): Location
        locations: [Location]
        qrCode(id: Int!): QrCode
        qrExists(qr_code: String): Boolean
        product(id: Int!): Product
        products: [Product]
    }
    """
)
