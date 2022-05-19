CREATE TABLE account (
    Id int, 
    Email VARCHAR(255) UNIQUE, 
    Password VARCHAR(255),
    Name VARCHAR(255),
    AccountType ENUM('admin', 'user'),
    PRIMARY KEY(Id)
);

CREATE TABLE survey (
    Id int, 
    ShortName VARCHAR(255),
    Name VARCHAR(255),
    Description VARCHAR(255),
    Created DATE, 
    LastUpdated DATE, 
    PRIMARY KEY(Id)
);

CREATE TABLE question (
    Id int,
    SurveyId int,
    Question VARCHAR(255), 
    QuestionType int,
    ProfileCharacteristic VARCHAR(255),
    Note VARCHAR(255),
    PRIMARY KEY(Id, SurveyId),
    FOREIGN KEY (SurveyId) REFERENCES survey(Id)
);

CREATE TABLE questionAcceptableAnswer (
    SurveyId int,
    questionNumber int,
    answerValue VARCHAR(255), 
    questionType ENUM('multiple', 'single'),
    PRIMARY KEY (SurveyId, questionNumber),
	FOREIGN KEY (questionNumber) REFERENCES question(Id),
    FOREIGN KEY (SurveyId) REFERENCES survey(Id)
);

CREATE TABLE response (
	RId int,
    UId int,
    answeredAt DATE,
    PRIMARY KEY(RId),
    FOREIGN KEY (UId) REFERENCES account(id)
);

CREATE TABLE answers (
	AnsId int,
    answerValue VARCHAR(255) NOT NULL,
    PRIMARY KEY(AnsId)
);

CREATE TABLE profile (
	PId int,
    PRIMARY KEY(PId)
);

CREATE TABLE criteria (
    CId int,
	cName VARCHAR(255),
    cValue int,
    cDescription VARCHAR(255),
    PRIMARY KEY(CId)
);

CREATE TABLE onet (
	ONId int,
    ODescription VARCHAR(255) NOT NULL,
    PRIMARY KEY(ONId)
);

CREATE TABLE feautures (
	FId int,
    featuredValue VARCHAR(255) NOT NULL,
    PRIMARY KEY(FId)
);

CREATE TABLE accountProfile (
	AId int,
    PId int,
    FOREIGN KEY (AId) REFERENCES account(id),
    FOREIGN KEY (PId) REFERENCES profile(PId),
    UNIQUE(AId, PId)
);

CREATE TABLE responseProfile (
	RId int,
    PId int,
    FOREIGN KEY (RId) REFERENCES response(RId),
    FOREIGN KEY (PId) REFERENCES profile(PId),
    UNIQUE(RId, PId)
);

CREATE TABLE jobProfile (
	JId int,
    profileId int,
	jobName VARCHAR(255) NOT NULL,
    FOREIGN KEY(profileId) REFERENCES profile(PId),
    PRIMARY KEY(JId)
);

CREATE TABLE jobFeatures (
	ONId int,
    FeaturedId int,
    FOREIGN KEY (ONId) REFERENCES onet(ONId),
    FOREIGN KEY (FeaturedId) REFERENCES feautures(FId),
    UNIQUE(ONId, FeaturedId)
);

CREATE TABLE desiredProfileCriteria (
	CId int,
    importanceRating int NOT NULL,
    FOREIGN KEY (CId) REFERENCES criteria(CId)
);

CREATE TABLE oNETProfileCriteria (
	PId int,
	CId int,
    value int,
    FOREIGN KEY (PId) REFERENCES profile(PId),
    FOREIGN KEY (CId) REFERENCES criteria(CId)
);

CREATE TABLE surveyProfileCriteria (
	PId int,
	CId int,
    value int,
    FOREIGN KEY (PId) REFERENCES profile(PId),
    FOREIGN KEY (CId) REFERENCES criteria(CId)
);

CREATE TABLE surveyResponse (
	qNumber int,
    aNumber int,
    FOREIGN KEY (qNumber) REFERENCES answers(AnsId),
    FOREIGN KEY (aNumber) REFERENCES question(Id),
    UNIQUE(qNumber, aNumber)
);

