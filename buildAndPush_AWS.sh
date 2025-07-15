docker build -t sidehustle .
docker tag sidehustle:latest 649207544517.dkr.ecr.us-east-1.amazonaws.com/sidehustle:latest
docker push 649207544517.dkr.ecr.us-east-1.amazonaws.com/sidehustle:latest