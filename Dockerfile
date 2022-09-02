FROM python:3.8-slim
WORKDIR ./
COPY . .

# arguments are not handled, if you want to change parameters use the command below
# "docker run image_tag python3 mortgage.py -v VALUE -l LEN" ... etc
# run: "docker run image_tag python3 mortgage.py -h" for a help
CMD ["python3", "mortgage.py"]
