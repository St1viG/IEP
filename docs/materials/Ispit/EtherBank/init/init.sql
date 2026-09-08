DROP DATABASE IF EXISTS ether_bank_database;
CREATE DATABASE ether_bank_database;
USE ether_bank_database;

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;
DROP TABLE IF EXISTS user_role;
DROP TABLE IF EXISTS accounts;

CREATE TABLE users (
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email varchar(256) NOT NULL UNIQUE,
    password varchar(256) NOT NULL,
    account_address varchar(64) NOT NULL
);

CREATE TABLE roles (
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name varchar ( 256 ) NOT NULL
);

CREATE TABLE user_role (
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id int NOT NULL,
    role_id int NOT NULL,
    FOREIGN KEY ( user_id ) REFERENCES users ( id ),
    FOREIGN KEY ( role_id ) REFERENCES roles ( id )
);

CREATE TABLE accounts (
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id int NOT NULL,
    contract_address varchar(64) NOT NULL,
    FOREIGN KEY ( user_id ) REFERENCES users ( id )
);

insert into roles ( id, name ) values ( 1, "administrator" );
insert into roles ( id, name ) values ( 2, "user" );
insert into users ( id, email, password, account_address ) values ( 1, "admin@google.com", "1", "0xB6977beDcC511709bFD04Db8eef768086Df2b17a" );
insert into user_role ( user_id, role_id ) values ( 1, 1 );
