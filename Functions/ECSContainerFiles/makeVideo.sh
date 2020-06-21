#!/bin/bash
env
localAudioURL=`echo $AUDIO_URL | awk -F '/' '{print $NF}'`
localImageURL=`echo $IMAGE_URL | awk -F '/' '{print $NF}'`
echo $localAudioURL
echo $localImageURL
# Turn book name into a valid file name
localVideoURL=`echo $BOOK_NAME | sed 's/ \+/_/g' | sed 's/[^a-zA-Z0-9_]//g'`'.mp4'
echo $localVideoURL
# Download audio and image files from S3
echo Downloading audio from s3://$AUDIO_URL
aws s3 cp s3://$AUDIO_URL $localAudioURL
echo Downloading image from s3://$IMAGE_URL
aws s3 cp s3://$IMAGE_URL $localImageURL
# Combine to make video
ffmpeg -i $localImageURL -i $localAudioURL ./$localVideoURL
echo Copying video to bucket
aws s3 cp $localVideoURL s3://$VIDEO_S3_BUCKET