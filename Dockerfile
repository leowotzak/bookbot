FROM umihico/aws-lambda-selenium-python:latest

# Install required modules
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

# Copy function code
COPY lambda_function.py ./

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_function.handler" ]