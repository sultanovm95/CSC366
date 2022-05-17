CREATE TABLE account (
    id int, 
    Email VARCHAR(255) UNIQUE, 
    Passowrd VARCHAR(255),
    accountType ENUM('admin', 'user'),
    PRIMARY KEY(id)
);

CREATE TABLE survey (
    SurveyId int, 
    createdAt DATE, 
    lastUpdatedAt DATE, 
    PRIMARY KEY(SurveyId)
);

CREATE TABLE question (
    QId int,
    question VARCHAR(255), 
    questionType ENUM('multiple', 'single'),
    PRIMARY KEY(QId)
);

CREATE TABLE questionAcceptableAnswer (
    questionNumber int,
    answerValue VARCHAR(255), 
    questionType ENUM('multiple', 'single'),
	FOREIGN KEY (questionNumber) REFERENCES question(QId)
);

CREATE TABLE response (
	RId int,
    answeredAt DATE,
    PRIMARY KEY(RId)
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
    FOREIGN KEY (aNumber) REFERENCES question(QId),
    UNIQUE(qNumber, aNumber)
);

