localAudioURL=`echo $AUDIO_URL | awk -F '/' '{print $NF}'`
localImageURL=`echo $IMAGE_URL | awk -F '/' '{print $NF}'`
# Turn book name into a valid file name
localVideoURL=`echo $BOOK_NAME | sed 's/ \+/_/g' | sed 's/[^a-zA-Z0-9_]//g'`'.mp4'
# Download audio and video
aws s3 cp s3://$AUDIO_URL localAudioURL
aws s3 cp s3://$IMAGE_URL localImageURL
ffmpeg -i localImageURL -i localAudioURL localVideoURL
aws s3 cp localVideoURL s3://$VIDEO_S3_BUCKET