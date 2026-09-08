drop table if exists bonuses;
drop table if exists is_engaged;
drop table if exists employees;
drop table if exists tasks;

create table employees (
    id integer primary key autoincrement not null,
	forename varchar ( 64 ) not null,
	surname varchar ( 64 ) not null,
	email varchar ( 64 ) not null,
	gender int not null,
	position varchar ( 64 ) not null
);

create table tasks (
    id integer primary key autoincrement not null,
	description varchar ( 256 ) not null
);

create table is_engaged (
    employee_id int not null,
	task_id int not null,
	foreign key ( employee_id ) references employees ( id ),
	foreign key ( task_id ) references tasks ( id ),
	primary key ( employee_id, task_id )
);

create table bonuses (
    id integer primary key autoincrement not null,
	reason varchar ( 256 ) not null,
	amount float not null,
	employee_id int not null,
	foreign key ( employee_id ) references employees ( id )
);

insert into employees ( id, forename, surname, email, gender, position ) values ( 1, 'Waldon', 'Wearne', 'wwearne0@is.gd', 0, 'Account Executive' );
insert into employees ( id, forename, surname, email, gender, position ) values ( 2, 'Ric', 'Verbrugge', 'rverbrugge1@hc360.com', 0, 'Civil Engineer' );
insert into employees ( id, forename, surname, email, gender, position ) values ( 3, 'Letizia', 'Elintune', 'lelintune2@amazon.co.uk', 'Bigender', 'Nurse Practicioner' );
insert into employees ( id, forename, surname, email, gender, position ) values ( 4, 'Cinderella', 'Ivory', 'civory3@cisco.com', 1, 'Associate Professor' );
insert into employees ( id, forename, surname, email, gender, position ) values ( 5, 'Maudie', 'Maleney', 'mmaleney4@mlb.com', 1, 'Business Systems Development Analyst' );
insert into employees ( id, forename, surname, email, gender, position ) values ( 6, 'Whittaker', 'Kubasek', 'wkubasek5@wsj.com', 0, 'Statistician III' );
insert into employees ( id, forename, surname, email, gender, position ) values ( 7, 'Carissa', 'Licas', 'clicas6@ed.gov', 1, 'Product Engineer' );
insert into employees ( id, forename, surname, email, gender, position ) values ( 8, 'Antoine', 'Savidge', 'asavidge7@vinaora.com', 0, 'Accounting Assistant IV' );
insert into employees ( id, forename, surname, email, gender, position ) values ( 9, 'Flin', 'Moorman', 'fmoorman8@hexun.com', 0, 'Tax Accountant' );
insert into employees ( id, forename, surname, email, gender, position ) values ( 10, 'Ichabod', 'Keijser', 'ikeijser9@etsy.com', 0, 'Desktop Support Technician' );

insert into tasks ( id, description ) values ( 1, 'Quiquia velit amet neque amet aliquam dolorem etincidunt.' );
insert into tasks ( id, description ) values ( 2, 'Quaerat etincidunt velit ut quiquia voluptatem eius.' );
insert into tasks ( id, description ) values ( 3, 'Numquam quiquia magnam numquam adipisci amet magnam numquam.' );
insert into tasks ( id, description ) values ( 4, 'Dolor modi dolorem porro labore eius.' );
insert into tasks ( id, description ) values ( 5, 'Tempora dolorem magnam aliquam sit voluptatem ut.' );
insert into tasks ( id, description ) values ( 6, 'Non aliquam sit non etincidunt velit dolor.' );
insert into tasks ( id, description ) values ( 7, 'Quisquam velit ut ipsum.' );
insert into tasks ( id, description ) values ( 8, 'Modi quiquia aliquam modi quaerat porro.' );
insert into tasks ( id, description ) values ( 9, 'Non velit labore sed.' );
insert into tasks ( id, description ) values ( 10, 'Eius quaerat dolore porro.' );

insert into is_engaged ( employee_id, task_id ) values ( 1, 1 );
insert into is_engaged ( employee_id, task_id ) values ( 1, 2 );
insert into is_engaged ( employee_id, task_id ) values ( 1, 3 );
insert into is_engaged ( employee_id, task_id ) values ( 1, 4 );
insert into is_engaged ( employee_id, task_id ) values ( 1, 5 );
insert into is_engaged ( employee_id, task_id ) values ( 1, 6 );
insert into is_engaged ( employee_id, task_id ) values ( 1, 7 );
insert into is_engaged ( employee_id, task_id ) values ( 1, 9 );
insert into is_engaged ( employee_id, task_id ) values ( 1, 10 );
insert into is_engaged ( employee_id, task_id ) values ( 2, 3 );
insert into is_engaged ( employee_id, task_id ) values ( 2, 6 );
insert into is_engaged ( employee_id, task_id ) values ( 2, 9 );
insert into is_engaged ( employee_id, task_id ) values ( 3, 2 );
insert into is_engaged ( employee_id, task_id ) values ( 3, 4 );
insert into is_engaged ( employee_id, task_id ) values ( 3, 5 );
insert into is_engaged ( employee_id, task_id ) values ( 3, 7 );
insert into is_engaged ( employee_id, task_id ) values ( 3, 9 );
insert into is_engaged ( employee_id, task_id ) values ( 3, 10 );
insert into is_engaged ( employee_id, task_id ) values ( 4, 2 );
insert into is_engaged ( employee_id, task_id ) values ( 4, 3 );
insert into is_engaged ( employee_id, task_id ) values ( 4, 4 );
insert into is_engaged ( employee_id, task_id ) values ( 4, 6 );
insert into is_engaged ( employee_id, task_id ) values ( 4, 7 );
insert into is_engaged ( employee_id, task_id ) values ( 4, 8 );
insert into is_engaged ( employee_id, task_id ) values ( 4, 9 );
insert into is_engaged ( employee_id, task_id ) values ( 4, 10 );
insert into is_engaged ( employee_id, task_id ) values ( 5, 1 );
insert into is_engaged ( employee_id, task_id ) values ( 5, 3 );
insert into is_engaged ( employee_id, task_id ) values ( 5, 4 );
insert into is_engaged ( employee_id, task_id ) values ( 5, 5 );
insert into is_engaged ( employee_id, task_id ) values ( 5, 8 );
insert into is_engaged ( employee_id, task_id ) values ( 5, 10 );
insert into is_engaged ( employee_id, task_id ) values ( 6, 2 );
insert into is_engaged ( employee_id, task_id ) values ( 6, 3 );
insert into is_engaged ( employee_id, task_id ) values ( 6, 4 );
insert into is_engaged ( employee_id, task_id ) values ( 6, 6 );
insert into is_engaged ( employee_id, task_id ) values ( 6, 7 );
insert into is_engaged ( employee_id, task_id ) values ( 6, 8 );
insert into is_engaged ( employee_id, task_id ) values ( 6, 10 );
insert into is_engaged ( employee_id, task_id ) values ( 7, 2 );
insert into is_engaged ( employee_id, task_id ) values ( 7, 4 );
insert into is_engaged ( employee_id, task_id ) values ( 7, 7 );
insert into is_engaged ( employee_id, task_id ) values ( 7, 8 );
insert into is_engaged ( employee_id, task_id ) values ( 7, 9 );
insert into is_engaged ( employee_id, task_id ) values ( 7, 10 );
insert into is_engaged ( employee_id, task_id ) values ( 8, 1 );
insert into is_engaged ( employee_id, task_id ) values ( 8, 2 );
insert into is_engaged ( employee_id, task_id ) values ( 8, 3 );
insert into is_engaged ( employee_id, task_id ) values ( 8, 4 );
insert into is_engaged ( employee_id, task_id ) values ( 8, 5 );
insert into is_engaged ( employee_id, task_id ) values ( 8, 7 );
insert into is_engaged ( employee_id, task_id ) values ( 8, 8 );
insert into is_engaged ( employee_id, task_id ) values ( 8, 9 );
insert into is_engaged ( employee_id, task_id ) values ( 8, 10 );
insert into is_engaged ( employee_id, task_id ) values ( 9, 1 );
insert into is_engaged ( employee_id, task_id ) values ( 9, 6 );
insert into is_engaged ( employee_id, task_id ) values ( 9, 8 );
insert into is_engaged ( employee_id, task_id ) values ( 10, 5 );
insert into is_engaged ( employee_id, task_id ) values ( 10, 6 );
insert into is_engaged ( employee_id, task_id ) values ( 10, 7 );
insert into is_engaged ( employee_id, task_id ) values ( 10, 10 );

insert into bonuses ( id, reason, amount, employee_id ) values ( 1, 'SIGNING', 843.52, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 2, 'INITIATIVE', 173.51, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 3, 'SIGNING', 241.63, 4 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 4, 'LOYALTY', 323.65, 9 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 5, 'SIGNING', 806.2, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 6, 'INITIATIVE', 225.39, 10 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 7, 'SIGNING', 442.81, 9 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 8, 'INITIATIVE', 617.19, 10 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 9, 'SIGNING', 491.43, 7 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 10, 'LOYALTY', 404.61, 4 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 11, 'PERFOMANCE', 518.48, 2 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 12, 'PERFOMANCE', 965.31, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 13, 'SIGNING', 891.43, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 14, 'SIGNING', 251.02, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 15, 'PERFOMANCE', 890.38, 9 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 16, 'PERFOMANCE', 808.87, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 17, 'INITIATIVE', 986.61, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 18, 'INITIATIVE', 599.04, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 19, 'SIGNING', 350.42, 9 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 20, 'LOYALTY', 360.18, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 21, 'PERFOMANCE', 457.57, 4 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 22, 'INITIATIVE', 147.05, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 23, 'SIGNING', 688.23, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 24, 'INITIATIVE', 853.89, 10 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 25, 'PERFOMANCE', 803.96, 6 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 26, 'SIGNING', 486.18, 2 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 27, 'INITIATIVE', 878.72, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 28, 'PERFOMANCE', 374.8, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 29, 'SIGNING', 979.16, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 30, 'PERFOMANCE', 687.85, 2 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 31, 'PERFOMANCE', 685.65, 2 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 32, 'PERFOMANCE', 588.89, 8 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 33, 'PERFOMANCE', 615.97, 2 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 34, 'SIGNING', 851.18, 8 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 35, 'PERFOMANCE', 197.46, 9 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 36, 'INITIATIVE', 893.27, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 37, 'PERFOMANCE', 627.41, 10 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 38, 'SIGNING', 938.8, 10 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 39, 'LOYALTY', 840.27, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 40, 'LOYALTY', 826.95, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 41, 'LOYALTY', 877.47, 6 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 42, 'LOYALTY', 940.53, 9 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 43, 'SIGNING', 683.5, 4 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 44, 'LOYALTY', 215.64, 4 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 45, 'SIGNING', 214.65, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 46, 'LOYALTY', 236.52, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 47, 'PERFOMANCE', 304.84, 10 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 48, 'INITIATIVE', 276.43, 9 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 49, 'INITIATIVE', 700.23, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 50, 'INITIATIVE', 193.72, 6 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 51, 'SIGNING', 107.43, 9 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 52, 'SIGNING', 586.54, 8 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 53, 'INITIATIVE', 306.4, 6 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 54, 'SIGNING', 321.63, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 55, 'SIGNING', 622.61, 10 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 56, 'PERFOMANCE', 772.97, 2 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 57, 'PERFOMANCE', 890.09, 8 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 58, 'LOYALTY', 348.84, 6 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 59, 'PERFOMANCE', 953.1, 2 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 60, 'INITIATIVE', 980.32, 7 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 61, 'INITIATIVE', 200.03, 8 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 62, 'PERFOMANCE', 488.34, 7 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 63, 'SIGNING', 714.18, 8 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 64, 'SIGNING', 107.06, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 65, 'LOYALTY', 990.72, 4 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 66, 'LOYALTY', 578.36, 10 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 67, 'LOYALTY', 590.21, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 68, 'INITIATIVE', 762.63, 7 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 69, 'PERFOMANCE', 755.09, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 70, 'PERFOMANCE', 752.6, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 71, 'INITIATIVE', 652.43, 8 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 72, 'PERFOMANCE', 584.26, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 73, 'LOYALTY', 862.42, 8 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 74, 'SIGNING', 585.19, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 75, 'INITIATIVE', 649.87, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 76, 'LOYALTY', 645.68, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 77, 'LOYALTY', 780.93, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 78, 'LOYALTY', 901.04, 8 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 79, 'PERFOMANCE', 107.03, 9 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 80, 'LOYALTY', 973.16, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 81, 'INITIATIVE', 595.35, 9 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 82, 'LOYALTY', 949.14, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 83, 'INITIATIVE', 300.01, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 84, 'INITIATIVE', 584.31, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 85, 'PERFOMANCE', 343.8, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 86, 'SIGNING', 768.71, 10 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 87, 'INITIATIVE', 526.87, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 88, 'SIGNING', 371.91, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 89, 'INITIATIVE', 747.33, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 90, 'PERFOMANCE', 193.03, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 91, 'LOYALTY', 438.79, 10 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 92, 'SIGNING', 344.3, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 93, 'PERFOMANCE', 333.8, 5 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 94, 'PERFOMANCE', 691.15, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 95, 'LOYALTY', 943.2, 2 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 96, 'LOYALTY', 769.66, 2 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 97, 'SIGNING', 983.26, 1 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 98, 'SIGNING', 375.9, 8 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 99, 'LOYALTY', 891.11, 3 );
insert into bonuses ( id, reason, amount, employee_id ) values ( 100, 'PERFOMANCE', 203.66, 7 );
