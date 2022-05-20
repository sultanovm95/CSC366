SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS jobProfile;
DROP TABLE IF EXISTS profileCriteria;
DROP TABLE IF EXISTS surveyResponse;
DROP TABLE IF EXISTS account;
DROP TABLE IF EXISTS survey;
DROP TABLE IF EXISTS questionAcceptableAnswer;
DROP TABLE IF EXISTS question;
DROP TABLE IF EXISTS response;
DROP TABLE IF EXISTS answers;
DROP TABLE IF EXISTS profile;
DROP TABLE IF EXISTS criteria;
DROP TABLE IF EXISTS onet;
DROP TABLE IF EXISTS accountProfile;
DROP TABLE IF EXISTS responseProfile;

-- Drop Statements for old tables that may still be around
DROP TABLE IF EXISTS feautures;
DROP TABLE IF EXISTS oNETProfileCriteria;
DROP TABLE IF EXISTS desiredProfileCriteria;
DROP TABLE IF EXISTS surveyProfileCriteria;
-- Prof told us to remove and just redirect to page
-- Move some of the meta data that would go here to onet table
DROP TABLE IF EXISTS features;
DROP TABLE IF EXISTS jobFeatures;

SET FOREIGN_KEY_CHECKS = 1;