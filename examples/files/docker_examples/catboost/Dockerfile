FROM python:3.7-buster
RUN python3 -m pip install catboost
COPY boost.py /entrypoint
RUN chmod +x /entrypoint
CMD ["/entrypoint"]