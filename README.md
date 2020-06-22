# Audiobook Generator
Serverless application which converts text to audio, and creates a simple video with it. Uses a range of AWS services including SNS, S3, Lambda, ECS (Fargate variant), Polly and DynamoDB, and is built in Python, with some Bash used for the container. This has been a nice little experiment, however the text to speech quality simply isn't good enough to be of practical use so I haven't really done anything with it.

## Contents
* ./Infrastructure - the definition of the infrastructure needed to run this application using AWS's CDK framework
* ./Functions - contains the actual application code, resources for running locally, and the definition for the video processing container

## Flow
* .txt file is uploaded to the BookUploadBucket. This has a metadata section like the below:
```json
{
    "bookName": "The Red-Headed League", 
    "imageURL": "audiobook-imageuploadbucket49d95137-yv28ka4kfodk/A_Scandal_in_Bohemia-04.jpg",
    "authorName": "Arthur Conan Doyle",
    "genres": ["mystery", "adventure"],
    "description": ""
}
------ END METADATA --------
```
* HandleBookUploadLambda is triggered, asks Polly to record the audio, parses the metadata, and creates a record in the DynamoDB database in this format:
```json
{
    "id": "Random string",
    "bookName": "string",
    "imageURL": "string",
    "authorName": "string",
    "genres": ["genre 1", "genre 2"],
    "audioURLs":  ["URL for part 1", "URL for part 2"],
    "description": "string",
    "hidden": true/false,
    "hasShortPart": true/false,
    "addedAt": 12345678 // Date in Unix timestamp format
}
```
* Polly uploads the mp3 file to AudioUploadBucket and sends a notification to the PollySNSTopic
* HandlePollyAudioLambda receives the message, retrieves the record from the DB, and triggers the container.
* The container downloads the audio file and image (from the URL defined in the text file's metadata), uses ffmepg to combine them into a mp4 video and uploads that to the VideoUploadBucket

## Deploy 
#### Requires
* AWS cli
* AWS ADK (see AWS website for setup)
* Python3 and pip
#### Commands
```bash
cd Infrastructure
pip install -r requirements.txt
cdk deploy
```