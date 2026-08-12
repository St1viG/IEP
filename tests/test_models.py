import pytest
import sqlalchemy
from werkzeug.security import check_password_hash, generate_password_hash

from models import Role, User, UserRole, database

pytestmark = pytest.mark.integration


def seed_roles():
    director = Role(name="director")
    employee = Role(name="employee")

    database.session.add_all([director, employee])
    database.session.commit()

    return director, employee


def add_user(email="onlymoney@gmail.com", password="evenmoremoney", role=None):
    user = User(forename="Scrooge", surname="McDuck", email=email, password=password)

    if role is not None:
        user.roles.append(role)

    database.session.add(user)
    database.session.commit()

    return user


def test_role_assignment_round_trips(application):
    director, employee = seed_roles()
    add_user(role=employee)

    stored = User.query.filter(User.email == "onlymoney@gmail.com").first()

    assert [role.name for role in stored.roles] == ["employee"]
    assert [user.email for user in employee.users] == ["onlymoney@gmail.com"]
    assert director.users == []


def test_deleting_a_user_clears_the_junction_row_and_keeps_the_roles(application):
    director, employee = seed_roles()
    user = add_user(role=employee)

    assert UserRole.query.count() == 1

    database.session.delete(user)
    database.session.commit()

    assert User.query.count() == 0
    assert UserRole.query.count() == 0
    assert sorted(role.name for role in Role.query.all()) == ["director", "employee"]


def test_email_is_unique(application):
    director, employee = seed_roles()
    add_user(role=employee)

    database.session.add(
        User(forename="Donald", surname="Duck", email="onlymoney@gmail.com", password="quack")
    )

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        database.session.commit()


def test_password_column_holds_a_werkzeug_hash(application):
    director, employee = seed_roles()

    hashed = generate_password_hash("evenmoremoney")

    assert len(hashed) <= 256

    add_user(password=hashed, role=employee)

    stored = User.query.filter(User.email == "onlymoney@gmail.com").first()

    assert check_password_hash(stored.password, "evenmoremoney")
    assert not check_password_hash(stored.password, "evenmoremone")
