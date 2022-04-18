/*select * from shows where datediff(Date,curdate())<0 and timediff(cast(convert_tz(curtime(),'+00:00','+05:30') as time),cast(time*100 as time))<0;*/
/*DECLARE @casted time;*/
/*select * from shows where datediff(Date,cast(convert_tz(now(),'+00:00','+05:30') as date))<=0 and timediff(cast(convert_tz(cast(time*100 as time),'+00:00','+00:30') as time),cast(convert_tz(cast(now() as time),'+00:00','+05:30') as time))<0;
/*select cast(convert_tz(curtime(),'+00:00','+05:30') as time);*/
/*select cast(convert_tz(cast(1700*100 as time),'+00:00','+00:30') as time);*/
/*select time from shows where datediff(Date,cast(convert_tz(now(),'+00:00','+05:30') as date))>=0 and timediff(cast(convert_tz(cast(time*100 as time),'+00:00','+00:30') as time),cast(convert_tz(cast(121100 as time),'+00:00','+05:30') as time))<0;*/
/*use theatre_database;*/
/*create table temp(ti time);*/
/*insert into temp value('9:5');*/
/*select cast('2022/9/1 0:5' as datetime) as time_value;*/
/*select cast('2022/9/1 0:5' as time);*/
/*select convert(1700*100,time);*/
use theatre_database;

set foreign_key_checks=0;

drop table halls;
drop table movies;
drop table price_listing;
drop table shows;
drop table booked_tickets;
drop table types;

create table halls (hall_id int, class varchar(10), no_of_seats int, email varchar(100), foreign key(email) references theatre(email), primary key(email,class,hall_id));

create table movies (movie_id int primary key, movie_name varchar(40), length int, language varchar(10), show_start date, show_end date, division_name varchar(31), district varchar(30));

create table price_listing (price_id int, type varchar(3), day varchar(10), price int, email varchar(100), foreign key(email) references theatre(email), primary key(price_listing,email));

create table shows (show_id int primary key,movie_id int, hall_id int, type varchar(3), time int, Date date, price_id int, email varchar(100),
	foreign key(movie_id) references movies(movie_id), foreign key(price_id) references price_listing(price_id) on update cascade);

create table booked_tickets (ticket_no int, show_id int, seat_no int, email varchar(100), price float,
	foreign key(email) references user(email),foreign key(show_id) references shows(show_id) on delete cascade);

create table cancelled_tickets (ticket_no int, show_id int, seat_no int, email varchar(100), price float,
	foreign key(email) references user(email),foreign key(show_id) references shows(show_id) on delete cascade);

create table types(movie_id int primary key,type1 varchar(3),type2 varchar(3),type3 varchar(3),
	foreign key(movie_id) references movies(movie_id) on delete cascade);  

create table completed_tickets (ticket_no int, show_id int, seat_no varchar(2000), email varchar(100), price float, movie_name varchar(55), Date date, time int, status varchar(10));

set foreign_key_checks=1;

drop trigger get_price;
delimiter //

create trigger get_price
after insert on halls
for each row
begin

UPDATE shows s, price_listing p 
SET s.price_id=p.price_id 
WHERE p.price_id IN 
(SELECT price_id 
FROM price_listing p 
WHERE s.email=p.email AND dayname(s.Date)=p.day AND s.type=p.type);

end; //

delimiter ;


drop procedure delete_old;
delimiter //

create procedure delete_old()
begin

DELETE FROM coupoun_code where datediff(dates,cast(now() as date))<0;

DELETE FROM booked_tickets where show_id in (select show_id from shows where datediff(Date,cast(now() as date))<=0 and timediff(cast(convert_tz(cast(time*100 as time),'+00:00','+00:30') as time),cast(now() as time))<0);

DELETE FROM cancelled_tickets where show_id in (select show_id from shows where datediff(Date,cast(now() as date))<=0 and timediff(cast(convert_tz(cast(time*100 as time),'+00:00','+00:30') as time),cast(now() as time))<0);

DELETE FROM shows where datediff(Date,cast(now() as date))<=0 and timediff(cast(convert_tz(cast(time*100 as time),'+00:00','+00:30') as time),cast(now() as time))<0;

DELETE FROM booked_tickets where show_id in (select show_id from shows where movie_id in (SELECT movie_id FROM movies WHERE datediff(show_end,cast(now() as date))<0));

DELETE FROM cancelled_tickets where show_id in (select show_id from shows where movie_id in (SELECT movie_id FROM movies WHERE datediff(show_end,cast(now() as date))<0));

DELETE FROM shows WHERE movie_id IN (SELECT movie_id FROM movies WHERE datediff(show_end,cast(now() as date))<0);

DELETE FROM movies WHERE datediff(show_end,cast(now() as date))<0;

update completed_tickets set status="Complete" where status="Booked" and datediff(Date,cast(now() as date))<=0 and timediff(cast(convert_tz(cast(time*100 as time),'+00:00','+00:30') as time),cast(now() as time))<0;

end; //

delimiter ;
