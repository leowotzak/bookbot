# BookBot

### Automated tee time booking

Test the current __live__ lambda function
```bash
aws lambda invoke --function-name bookTeeTime response.json
```
<hr>

Build the lambda function docker image
```bash
docker build . --file Dockerfile --platform linux/amd64 -t bookbot:latest
```

Tag the image
```bash
docker tag bookbot:latest 851272982543.dkr.ecr.us-east-1.amazonaws.com/bookbot:latest
```

Push the image
```bash
docker push 851272982543.dkr.ecr.us-east-1.amazonaws.com/bookbot:latest
```
