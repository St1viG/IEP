from flask import Flask

from flask_migrate import Migrate

from werkzeug.security import generate_password_hash

from configuration import Configuration

from models import database
from models import Role
from models import User

DIRECTOR = {
    "forename": "Scrooge",
    "surname":  "McDuck",
    "email":    "onlymoney@gmail.com",
    "password": "evenmoremoney"
}

application = Flask ( __name__ )
application.config.from_object ( Configuration )

database.init_app ( application )

migrate = Migrate ( application, database )

with application.app_context ( ):
    database.create_all ( )

    # Kubernetes retries a failed Job, so every write below has to be a no-op
    # the second time around.
    roles = { }

    for name in [ "director", "employee" ]:
        role = Role.query.filter ( Role.name == name ).first ( )

        if ( role is None ):
            role = Role ( name = name )
            database.session.add ( role )

        roles[name] = role

    database.session.commit ( )

    if ( User.query.filter ( User.email == DIRECTOR["email"] ).first ( ) is None ):
        director = User (
            forename = DIRECTOR["forename"],
            surname  = DIRECTOR["surname"],
            email    = DIRECTOR["email"],
            password = generate_password_hash ( DIRECTOR["password"] )
        )

        director.roles.append ( roles["director"] )

        database.session.add ( director )
        database.session.commit ( )
