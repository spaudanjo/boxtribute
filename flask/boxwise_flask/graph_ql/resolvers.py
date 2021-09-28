"""GraphQL resolver functionality"""
from ariadne import (
    EnumType,
    MutationType,
    ObjectType,
    ScalarType,
    convert_kwargs_to_snake_case,
    gql,
    make_executable_schema,
    snake_case_fallback_resolvers,
)
from boxwise_flask.auth_helper import authorization_test
from boxwise_flask.graph_ql.mutation_defs import mutation_defs
from boxwise_flask.graph_ql.query_defs import query_defs
from boxwise_flask.graph_ql.type_defs import type_defs
from boxwise_flask.models.base import Base
from boxwise_flask.models.box import Box, create_box, update_box
from boxwise_flask.models.location import Location
from boxwise_flask.models.organisation import Organisation
from boxwise_flask.models.product import Product
from boxwise_flask.models.product_category import ProductCategory
from boxwise_flask.models.qr_code import QRCode
from boxwise_flask.models.size import Size
from boxwise_flask.models.user import User

from flask import g

query = ObjectType("Query")
box = ObjectType("Box")
product = ObjectType("Product")
user = ObjectType("User")
mutation = MutationType()

datetime_scalar = ScalarType("Datetime")
date_scalar = ScalarType("Date")


@datetime_scalar.serializer
def serialize_datetime(value):
    return value.isoformat()


@date_scalar.serializer
def serialize_date(value):
    return value.isoformat()


@query.field("bases")
def resolve_bases(_, info):
    return Base.select().where(Base.id.in_(g.user["base_ids"]))


@query.field("base")
def resolve_base(_, info, id):
    authorization_test("bases", base_id=id)
    return Base.get_by_id(id)


@query.field("users")
def resolve_users(_, info):
    return User.select()


@query.field("user")
def resolve_user(_, info, email):
    data = User.select().where(User.email == email).dicts().get()
    data["organisation"] = Organisation.get_by_id(g.user["organisation_id"])
    data["bases"] = Base.select().where(Base.id.in_(g.user["base_ids"]))
    return data


@query.field("qrExists")
@convert_kwargs_to_snake_case
def resolve_qr_exists(_, info, qr_code):
    try:
        QRCode.get_id_from_code(qr_code)
    except QRCode.DoesNotExist:
        return False
    return True


@query.field("qrCode")
@convert_kwargs_to_snake_case
def resolve_qr_code(_, info, qr_code):
    data = QRCode.select().where(QRCode.code == qr_code).dicts().get()
    data["box"] = Box.get(Box.qr_code == data["id"])
    return data


@query.field("product")
def resolve_product(_, info, id):
    product = Product.get_by_id(id)
    authorization_test("bases", base_id=str(product.base.id))
    return product


@query.field("box")
@convert_kwargs_to_snake_case
def resolve_box(_, info, box_id):
    return Box.get(Box.box_label_identifier == box_id)


@query.field("location")
def resolve_location(_, info, id):
    data = Location.select().where(Location.id == id).dicts().get()
    authorization_test("bases", base_id=str(data["base"]))
    data["boxes"] = Box.select().where(Box.location == id)
    return data


@query.field("organisation")
def resolve_organisation(_, info, id):
    authorization_test("organisation", organisation_id=id)
    data = Organisation.select().where(Organisation.id == id).dicts().get()
    data["bases"] = Base.select().where(Base.organisation_id == id)
    return data


@query.field("productCategory")
def resolve_product_category(_, info, id):
    data = ProductCategory.select().where(ProductCategory.id == id).dicts().get()
    data["products"] = Product.select().where(Product.category == id)
    return data


@query.field("productCategories")
def resolve_product_categories(_, info):
    return ProductCategory.select()


@query.field("organisations")
def resolve_organisations(_, info):
    return Organisation.select()


@query.field("locations")
def resolve_locations(_, info):
    return Location.select()


@query.field("products")
def resolve_products(_, info):
    return Product.select()


@box.field("state")
def resolve_box_state(obj, info):
    # Instead of a BoxState instance return an integer for EnumType conversion
    return obj.box_state.id


@mutation.field("createBox")
@convert_kwargs_to_snake_case
def resolve_create_box(_, info, box_creation_input):
    user_id = User.get(User.email == g.user["email"]).id
    box_creation_input["created_by"] = user_id
    return create_box(box_creation_input)


@mutation.field("updateBox")
@convert_kwargs_to_snake_case
def resolve_update_box(_, info, box_update_input):
    user_id = User.get(User.email == g.user["email"]).id
    box_update_input["last_modified_by"] = user_id
    return update_box(box_update_input)


@product.field("gender")
def resolve_product_gender(obj, info):
    return obj.id


@product.field("sizes")
def resolve_sizes(product_id, info):
    product = Product.get_by_id(product_id)
    sizes = Size.select(Size.label).where(Size.seq == product.size_range.seq)
    return [size.label for size in sizes]


# Translate GraphQL enum into id field of database table
product_gender_type_def = EnumType(
    "ProductGender",
    {
        "Women": 1,
        "UnisexAdult": 3,
    },
)
box_state_type_def = EnumType(
    "BoxState",
    {
        "InStock": 1,
    },
)


schema = make_executable_schema(
    gql(type_defs + query_defs + mutation_defs),
    [
        query,
        mutation,
        date_scalar,
        datetime_scalar,
        box,
        product,
        user,
        product_gender_type_def,
        box_state_type_def,
    ],
    snake_case_fallback_resolvers,
)
