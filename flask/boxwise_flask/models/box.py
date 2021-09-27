import uuid
from datetime import datetime

from boxwise_flask.db import db
from boxwise_flask.models.box_state import BoxState
from boxwise_flask.models.location import Location
from boxwise_flask.models.product import Product
from boxwise_flask.models.size import Size
from boxwise_flask.models.user import User
from peewee import (
    SQL,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    TextField,
)

from .qr_code import QRCode


class Box(db.Model):
    box_label_identifier = CharField(
        column_name="box_id",
        constraints=[SQL("DEFAULT ''")],
        index=True,
        unique=True,
        max_length=11,
    )
    box_state = ForeignKeyField(
        column_name="box_state_id",
        constraints=[SQL("DEFAULT 1")],
        field="id",
        model=BoxState,
        on_update="CASCADE",
    )
    comment = TextField(column_name="comments")
    created_on = DateTimeField(column_name="created", null=True)
    created_by = ForeignKeyField(
        column_name="created_by",
        field="id",
        model=User,
        null=True,
        on_delete="SET NULL",
        on_update="CASCADE",
        constraints=[SQL("UNSIGNED")],
    )
    deleted = DateTimeField(null=True, default=None)
    items = IntegerField()
    location = ForeignKeyField(
        column_name="location_id",
        field="id",
        model=Location,
        on_update="CASCADE",
    )
    last_modified_on = DateTimeField(column_name="modified", null=True)
    last_modified_by = ForeignKeyField(
        column_name="modified_by",
        field="id",
        model=User,
        null=True,
        on_delete="SET NULL",
        on_update="CASCADE",
        constraints=[SQL("UNSIGNED")],
    )
    ordered = DateTimeField(null=True)
    ordered_by = ForeignKeyField(
        column_name="ordered_by",
        field="id",
        model=User,
        null=True,
        on_delete="SET NULL",
        on_update="CASCADE",
        constraints=[SQL("UNSIGNED")],
    )
    picked = IntegerField(null=True)
    picked_by = ForeignKeyField(
        column_name="picked_by",
        field="id",
        model=User,
        null=True,
        on_delete="SET NULL",
        on_update="CASCADE",
        constraints=[SQL("UNSIGNED")],
    )
    product = ForeignKeyField(
        column_name="product_id",
        field="id",
        model=Product,
        on_update="CASCADE",
    )
    qr_code = ForeignKeyField(
        column_name="qr_id",
        field="id",
        model=QRCode,
        null=True,
        on_update="CASCADE",
        unique=True,
        constraints=[SQL("UNSIGNED")],
    )
    size = ForeignKeyField(
        column_name="size_id",
        field="id",
        model=Size,
        null=True,
        on_update="CASCADE",
        constraints=[SQL("UNSIGNED")],
    )

    class Meta:
        table_name = "stock"

    def __unicode__(self):
        return self.box_label_identifier

    @staticmethod
    def get_box(box_id):
        return Box.get(Box.box_label_identifier == box_id)


def create_box(box_creation_input):
    """Insert information for a new Box in the database. Use current datetime
    and box state "InStock" by default. Generate a UUID to identify the box.
    """
    now = datetime.utcnow()
    qr_code = box_creation_input.pop("qr_code", None)
    qr_id = QRCode.get_id_from_code(qr_code) if qr_code is not None else None

    new_box = Box.create(
        box_label_identifier=str(uuid.uuid4())[: Box.box_label_identifier.max_length],
        qr_id=qr_id,
        created_on=now,
        last_modified_on=now,
        last_modified_by=box_creation_input["created_by"],
        box_state=1,
        **box_creation_input,
    )
    return new_box


def update_box(box_update_input):
    """Look up an existing Box given a UUID, and update all requested fields.
    Insert timestamp for modification and return the box.
    """
    box_id = box_update_input.pop("box_label_identifier")
    box = Box.get_box(box_id)

    for field, value in box_update_input.items():
        setattr(box, field, value)

    box.last_modified_on = datetime.utcnow()
    box.save()
    return box
