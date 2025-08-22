-- after using SQL Server Management Studio to create the database, run this script to set up the desired tables
CREATE TABLE USERS (
	USER_ID INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
	USERNAME VARCHAR(80) NOT NULL,
	PASSWORD VARCHAR(4096) NOT NULL
);

-- note that table USERS is also a system table, so it may be that for some operations you need to use the full syntax, e.g., [EllipsoidLabs].dbo.USERS