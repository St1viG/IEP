import os
import re

from datetime import datetime

from flask import Flask
from flask import request
from flask import jsonify

from flask_jwt_extended import JWTManager

from pymongo import MongoClient

from configuration import Configuration

from decorators import role_check

application = Flask ( __name__ )
application.config.from_object ( Configuration )

jwt = JWTManager ( application )

client = MongoClient (
    host       = Configuration.MONGO_HOST,
    port       = Configuration.MONGO_PORT,
    username   = Configuration.MONGO_USERNAME,
    password   = Configuration.MONGO_PASSWORD,
    authSource = Configuration.MONGO_AUTH_SOURCE
)

assets = client[Configuration.MONGO_DATABASE][Configuration.MONGO_ASSETS]


def parse_iso ( value ):
    return datetime.fromisoformat ( value.replace ( "Z", "+00:00" ) )


def format_iso ( value ):
    return value.isoformat ( timespec = "milliseconds" ) + "Z"


def serialize ( asset ):
    serialized = {
        "id":           str ( asset["_id"] ),
        "name":         asset["name"],
        "categories":   asset["categories"],
        "buying_price": asset["buying_price"],
        "buying_date":  format_iso ( asset["buying_date"] ),
        "info":         asset.get ( "info", { } )
    }

    if ( "selling_price" in asset ):
        serialized["selling_price"] = asset["selling_price"]

    if ( "selling_date" in asset ):
        serialized["selling_date"] = format_iso ( asset["selling_date"] )

    return serialized


@application.route ( "/search", methods = ["POST"] )
@role_check ( "employee" )
def search ( ):
    body = request.get_json ( silent = True ) or { }

    name         = body.get ( "name" )
    category     = body.get ( "category" )
    buying_date  = body.get ( "buying_date" )
    selling_date = body.get ( "selling_date" )
    info_filters = body.get ( "info_filters" ) or [ ]

    conditions = [ ]

    if ( name is not None ):
        conditions.append ( { "name": { "$regex": re.escape ( name ) } } )

    if ( category is not None ):
        conditions.append ( { "categories": category } )

    if ( buying_date is not None ):
        conditions.append ( { "buying_date": { "$gt": parse_iso ( buying_date ) } } )

    if ( selling_date is not None ):
        conditions.append ( { "selling_date": { "$lt": parse_iso ( selling_date ) } } )

    for info_filter in info_filters:
        field    = info_filter["field"]
        operator = info_filter["operator"]
        value    = info_filter["value"]

        conditions.append ( { f"info.{field}": { f"${operator}": value } } )

    query = { "$and": conditions } if ( len ( conditions ) > 0 ) else { }

    return jsonify ( assets = [ serialize ( asset ) for asset in assets.find ( query ) ] )


if ( __name__ == "__main__" ):
    PORT = os.environ["PORT"] if ( "PORT" in os.environ ) else "5000"

    application.run ( debug = True, port = PORT, host = Configuration.HOST )
