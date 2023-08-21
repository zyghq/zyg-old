import logging

# @sanchitrk
# Note: I'm not sure I want to do this, but I'm going to do it for now.
# logger should be more generic, here it's tied to uvicorn.
# if there is a way to get uniform logger that would be better.
logger = logging.getLogger("uvicorn")

# make sqlalchemy logger use uvicorn logger
logging.getLogger("sqlalchemy").addHandler(logger)
