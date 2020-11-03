FROM python:3
WORKDIR /service
RUN pip3 install kubernetes requests
ENTRYPOINT ["python3"]
ADD service.py /service/
CMD ["service.py"]
