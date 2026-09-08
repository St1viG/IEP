create database users;
use users;

create table user (
    id int primary key,
    username varchar(256) not null,
    password varchar(256) not null
);

insert into user values ( 1, "user0", "pass0" );
insert into user values ( 2, "user1", "pass1" );
insert into user values ( 3, "user2", "pass2" );
insert into user values ( 4, "user3", "pass3" );
