CREATE TABLE account (
    Id int, 
    Email VARCHAR(255) UNIQUE, 
    Password VARCHAR(255),
    Name VARCHAR(255),
    AccountType ENUM('admin', 'user'),
    PRIMARY KEY (Id)
);

CREATE TABLE survey (
    Id int, 
    ShortName VARCHAR(255),
    Name VARCHAR(255),
    Description VARCHAR(255),
    CreatedDate DATE, 
    LastUpdated DATE, 
    PRIMARY KEY (Id)
);

CREATE TABLE question (
    Id int,
    SurveyId int,
    Question VARCHAR(255), 
    QuestionType int,
    ProfileCharacteristic VARCHAR(255),
    Note VARCHAR(255),
    PRIMARY KEY (Id, SurveyId),
    FOREIGN KEY (SurveyId) REFERENCES survey(Id)
);

CREATE TABLE questionAcceptableAnswer (
    SurveyId int,
    QuestionId int,
    AnswerValue VARCHAR(255),
    AnswerText VARCHAR(255),
    Comment VARCHAR(255),
    PRIMARY KEY (SurveyId, QuestionId, AnswerValue),
	FOREIGN KEY (QuestionId) REFERENCES question(Id),
    FOREIGN KEY (SurveyId) REFERENCES survey(Id)
);

CREATE TABLE profile (
    PId int,
    PType ENUM('Desired', 'ONET', 'Experience'),
    PName VARCHAR(255),
    PRIMARY KEY (PId)
);

CREATE TABLE response (
	Id int,
    UserId int,
    SurveyId int,
    SurveyProfile int,
    AnswerDate DATE,
    PRIMARY KEY (Id),
    FOREIGN KEY (UserId) REFERENCES account(Id),
    FOREIGN KEY (SurveyId) REFERENCES survey(Id),
    FOREIGN KEY (SurveyProfile) REFERENCES profile(PId)
);

CREATE TABLE onet (
    ONetId VARCHAR(255),
    ONetJob VARCHAR(255) NOT NULL,
    ONetProfile int,
    ONetDescription VARCHAR(255) NOT NULL,
    PRIMARY KEY(ONetId),
    FOREIGN KEY (ONetProfile) REFERENCES profile(PId)
);

CREATE TABLE answers (
	QuestionId int,
    ResponseId int,
    AnswerValue VARCHAR(255) NOT NULL,
    PRIMARY KEY (QuestionId, ResponseId),
    FOREIGN KEY (QuestionId) REFERENCES question(Id),
    FOREIGN KEY (ResponseId) REFERENCES response(Id)
);

CREATE TABLE criteria (
    CId int,
	cName VARCHAR(255),
    cDescription TEXT,
    cCategory VARCHAR(255),
    PRIMARY KEY(CId)
);

CREATE TABLE accountProfile (
    AId int,
    PId int,
    FOREIGN KEY (AId) REFERENCES account(id),
    FOREIGN KEY (PId) REFERENCES profile(PId),
    PRIMARY KEY (PId)
);

CREATE TABLE profileCriteria (
	CId int,
    PId int,
    cValue int NOT NULL,
    importanceRating int NOT NULL,
    FOREIGN KEY (CId) REFERENCES criteria(CId),
    FOREIGN KEY (PId) REFERENCES profile(PId),
    PRIMARY Key(PId, CId)
);

