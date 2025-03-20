BEGIN;

CREATE TABLE State (
	ID			varchar(2) not null,
	Name			varchar(30) not null,

	Primary Key		(ID)
);

CREATE TABLE Address (
	ID			serial not null,
	Street			varchar(30) not null,
	City			varchar(20) not null,
	StateID			varchar(2) not null,
	Zip			varchar(5) not null,

	Primary Key		(ID),
	Foreign Key		(StateID) references State(ID)
				Deferrable Initially Deferred	
);

CREATE TABLE Student (
	ID			serial not null,
	Number			varchar(10) not null unique,
	FirstName		varchar(30) not null,
	LastName		varchar(30) not null,
	AddressID		integer not null,
	Grade			varchar(1) not null,

	Primary Key		(ID),
	Foreign Key		(AddressID) references Address(ID)
				Deferrable Initially Deferred
);

CREATE TABLE Guardian (
	ID			serial not null,
	Number			varchar(10) not null unique,
	FirstName		varchar(30) not null,
	LastName		varchar(30) not null,
	Email			varchar(40),
	PhoneNumber		varchar(15) not null,
	AddressID		integer not null,

	Primary Key		(ID),
	Foreign Key		(AddressID) references Address(ID)
				Deferrable Initially Deferred
);	

CREATE TABLE GuardianToStudent (
	StudentID		integer not null,
	GuardianID		integer not null,

	Primary Key 		(StudentID, GuardianID),
	Foreign Key 		(StudentID) references Student(ID)
				Deferrable Initially Deferred,
	Foreign Key		(GuardianID) references Guardian(ID)
				Deferrable Initially Deferred
);

CREATE TABLE StaffType (
	ID			varchar(3) not null,
	Name			varchar(20) not null,
	AdminAccess		boolean not null,

	Primary Key		(ID)
);

CREATE TABLE Staff (
	ID			serial not null,
	Number			varchar(10) not null unique,
	FirstName		varchar(30) not null,
	LastName		varchar(30) not null,
	PhoneNumber		varchar(15) not null,
	WorkEmail 		varchar(40) not null unique,
	StaffTypeID		varchar(3) not null,
	AddressID		integer not null,

	Primary Key		(ID),
	Foreign Key		(StaffTypeID) references StaffType(ID)
				Deferrable Initially Deferred,
	Foreign Key		(AddressID) references Address(ID)
				Deferrable Initially Deferred
);

CREATE TABLE Substitute (
	ID			serial not null,
	Number			varchar(10) not null unique,
	FirstName		varchar(30) not null,
	LastName		varchar(30) not null,
	PhoneNumber		varchar(15),
	WorkEmail 		varchar(40) not null unique,
	AddressID		integer not null,

	Primary Key		(ID),
	Foreign Key		(AddressID) references Address(ID)
				Deferrable Initially Deferred
);

CREATE TABLE Availability (
	ID			serial not null,
	SubstituteID		integer not null,
	StartDate		date not null,
	EndDate			date not null,

	Primary Key 		(ID),
	Foreign Key		(SubstituteID) references Substitute(ID)
				Deferrable Initially Deferred
);

CREATE TABLE TimeOffRequest (
	ID			serial not null,
	StartDate		date not null,
	EndDate			date not null,
	Reason			varchar(50) not null,
	StaffID			integer not null,
	SubstituteID		integer,

	Primary Key		(ID),
	Foreign Key		(StaffID) references Staff(ID)
				Deferrable Initially Deferred,
	Foreign Key		(SubstituteID) references Substitute(ID)
				Deferrable Initially Deferred
);

CREATE TABLE Room (
	Number			varchar(5) not null,
	Capacity		integer not null,
	PhoneNumber		varchar(15) unique,
	
	Primary Key		(Number)
);

CREATE TABLE ClassType (
	ID			varchar(3) not null,
	Name			varchar(40) not null unique,

	Primary Key		(ID)
);

CREATE TABLE Class (
	ID			serial not null,
	Number			varchar(10) not null unique,
	ClassTypeID		varchar(3) not null,
	RoomNumber		varchar(5) not null,
	StartTime		time not null,
	Duration		interval not null,
	
	Primary Key		(ID),
	Foreign Key		(ClassTypeID) references ClassType(ID)
				Deferrable Initially Deferred,
	Foreign Key		(RoomNumber) references Room(Number)
				Deferrable Initially Deferred
);

CREATE TABLE StaffToClass (
	StaffID			integer not null,
	ClassID			integer not null,

	Primary Key		(StaffID, ClassID),
	Foreign Key		(StaffID) references Staff(ID)
				Deferrable Initially Deferred,
	Foreign Key		(ClassID) references Class(ID)
				Deferrable Initially Deferred
);

CREATE TABLE StudentToClass (
	StudentID		integer not null,
	ClassID			integer not null,

	Primary Key		(StudentID, ClassID),
	Foreign Key		(StudentID) references Student(ID)
				Deferrable Initially Deferred,
	Foreign Key		(ClassID) references Class(ID)
				Deferrable Initially Deferred
);

COMMIT;